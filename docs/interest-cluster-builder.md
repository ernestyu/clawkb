# SPEC: Interest Cluster Builder

## 1. 目标

实现一个可重复运行的兴趣簇构建器，用于从文章数据库中读取历史文章及其 embedding，生成一组稳定、可落盘、可被后续推荐系统直接使用的兴趣簇。

本版本支持两种聚类算法后端：

* `kmeans++`
* `hierarchical`

本版本支持可选 PCA 降维，并且 **PCA 维度不使用固定数值**，而是使用 **累计解释方差阈值** 自动选择维度。

本版本的输出必须继续兼容后续推荐逻辑：

* 每个兴趣簇最终必须有一个 **原始 1024 维空间中的质心**
* 每篇文章必须有一个最终簇归属
* 簇结果写入数据库表：

  * `interest_clusters`
  * `interest_cluster_members`
  * `interest_meta`

---

## 2. 非目标

本版本不做以下事情：

* 不实现在线增量聚类
* 不实现自动网格搜索超参数
* 不实现聚类结果可视化界面
* 不实现簇自动命名优化
* 不实现软 membership，`membership` 固定写 `1.0`

---

## 3. 关键设计原则

### 3.1 聚类空间和落库存储空间可以不同

这是本版本必须严格遵守的原则。

* 聚类算法可以运行在 **PCA 降维后的空间**
* 但最终写入数据库的簇质心，必须在 **原始 1024 维兴趣向量空间** 中重新计算

原因：

后续推荐逻辑中，新文章会构造同样的 1024 维兴趣向量，并与数据库中存储的簇质心计算相似度。
因此，簇质心必须与新文章向量处于同一个空间。

### 3.2 算法后端必须和数据准备层解耦

向量读取、兴趣向量构造、归一化、PCA、聚类、小簇处理、落库必须分层，不允许把算法逻辑和 SQL 或落库逻辑混写在一起。

### 3.3 输出格式统一

无论使用 `kmeans++` 还是 `hierarchical`，最后都必须统一输出：

* 每篇文章所属最终簇
* 每个簇的成员列表
* 每个簇在原始 1024 维空间的质心
* 最终写库结果

---

## 4. 输入数据定义

### 4.1 数据来源

文章来自主表 `articles`。
embedding 来自：

* `articles_vec`：摘要语义向量
* `articles_tag_vec`：TAG 语义向量

### 4.2 入选条件

仅满足以下条件的文章参与聚类：

* 未被删除
* 有摘要，且摘要非纯空白
* `articles_vec` 和 `articles_tag_vec` 至少存在一项

### 4.3 每条入选文章必须获得的数据

每条文章进入内存后，应至少包含：

* `article_id: int`
* `title: str`
* `summary_vec: np.ndarray | None`
* `tag_vec: np.ndarray | None`

向量维度预期均为 1024。

### 4.4 向量缺失策略

* 如果只有 `summary_vec`，则只使用 `summary_vec`
* 如果只有 `tag_vec`，则只使用 `tag_vec`
* 如果两者都有，则按权重混合
* 如果两者都没有，则该文章不参与聚类

---

## 5. 兴趣向量构造

### 5.1 语义定义

当前约定：

* `tag_vec`：由长摘要经 LLM 抽取 12 个 TAG 后，再将 TAG 列表做 embedding 得到
* `summary_vec`：由“长摘要 + TAG + 标题”做 embedding 得到

这两个向量都来自同一个 embedding 模型，维度均为 1024。

### 5.2 混合规则

对于同时具有 `summary_vec` 和 `tag_vec` 的文章：

[
v = (1 - w_{tag}) \cdot v_{summary} + w_{tag} \cdot v_{tag}
]

其中：

* `w_tag` 默认值 `0.75`
* 通过环境变量或 CLI 参数注入

### 5.3 归一化要求

这是必须实现的步骤。

#### 情况 A：同时有 `summary_vec` 和 `tag_vec`

处理顺序：

1. 分别对 `summary_vec` 和 `tag_vec` 做 L2 normalization
2. 按权重做线性混合
3. 对混合结果再次做 L2 normalization
4. 得到最终兴趣向量 `interest_vec_1024`

#### 情况 B：只存在一条支路

处理顺序：

1. 对该向量做 L2 normalization
2. 结果即为 `interest_vec_1024`

### 5.4 为什么需要这样做

虽然两个向量都来自同一模型，维度也相同，但输入文本形态不同：

* `tag_vec` 的输入是短关键词列表
* `summary_vec` 的输入是长摘要 + TAG + 标题

因此两类向量的模长分布未必相同。
如果不先分别归一化，则 `0.75 / 0.25` 的权重未必真正代表语义方向上的权重，而可能被向量模长偏移。

---

## 6. PCA 降维

### 6.1 总体策略

PCA 为可选步骤。
如果启用 PCA，则：

* PCA 只作用于聚类阶段
* 不作用于最终落库的质心空间

### 6.2 启用条件

新增参数：

* `use_pca: bool`

默认建议：`true`

### 6.3 PCA 输入

PCA 的输入必须是整批文章的 `interest_vec_1024`，也就是：

* 已完成支路归一化
* 已完成权重混合
* 已完成最终归一化

之后在整批 1024 维向量上拟合 PCA。

### 6.4 PCA 维度选择方式

本版本 **不允许使用手动固定维度**。
必须使用 **累计解释方差阈值** 自动选择维度。

新增参数：

* `pca_explained_variance_threshold: float`

典型取值：

* `0.90`
* `0.95`

### 6.5 自动选维规则

设 PCA 全部拟合后得到累计解释方差数组：

[
c_1, c_2, \dots, c_d
]

选择最小的 `k`，使得：

[
c_k \ge \text{pca_explained_variance_threshold}
]

然后：

* 只保留前 `k` 个主成分
* 得到每篇文章的 `interest_vec_cluster`

### 6.6 边界要求

* `k` 至少为 `1`
* `k` 不得超过原始维度 `1024`
* 若样本数太小导致 PCA 实际可用维度小于目标，则使用 PCA 可用的最大维度

### 6.7 输出要求

日志中必须记录：

* PCA 是否启用
* 原始维度
* 自动选择出的维度 `k`
* 目标累计解释方差阈值
* 实际累计解释方差

### 6.8 重要约束

**聚类可以在 PCA 空间里做，但最终簇质心必须使用原始 1024 维兴趣向量重新计算。**

这个规则不允许违反。

---

## 7. 聚类算法切换

### 7.1 支持算法

本版本支持：

* `kmeans++`
* `hierarchical`

### 7.2 参数入口

新增统一参数：

* `cluster_algo: str`

合法值：

* `"kmeans++"`
* `"hierarchical"`

默认值建议：

* `"kmeans++"`

### 7.3 统一接口要求

实现一个统一入口函数：

```python
build_interest_clusters(config: InterestClusterConfig) -> BuildInterestClustersResult
```

内部流程固定为：

1. 加载数据
2. 构造原始 1024 维兴趣向量
3. 可选 PCA
4. 根据 `cluster_algo` 调用对应聚类后端
5. 统一执行小簇处理
6. 用原始 1024 维向量重算最终质心
7. 写库
8. 输出日志与统计

---

## 8. k-means++ 后端规范

### 8.1 输入

输入向量为：

* 若 `use_pca = true`：`interest_vec_cluster`（PCA 空间）
* 若 `use_pca = false`：`interest_vec_1024`

### 8.2 初始簇数计算

k-means++ 仍然需要初始簇数 `k0`。

新增参数：

* `min_cluster_size: int`
* `max_clusters: int`

初始计算规则：

[
k_0 = \min(\text{max_clusters}, \max(1, \lfloor n / \text{min_cluster_size} \rfloor))
]

其中：

* `n` 为参与聚类的文章数

边界处理：

* `n == 0`：直接返回空结果
* `n < min_cluster_size`：直接生成单簇
* `k0 > n`：截断为 `n`

### 8.3 k-means++ 参数

新增参数：

* `kmeans_random_state: int`
* `kmeans_n_init: int`
* `kmeans_max_iter: int`

建议默认值：

* `random_state = 42`
* `n_init = 10`
* `max_iter = 300`

### 8.4 初始化要求

必须使用标准 `k-means++` 初始化。
严禁继续使用“按查询顺序均匀抽点”的旧实现。

### 8.5 输出

k-means++ 输出：

* 每篇文章的簇标签 `labels`
* 初始簇中心（仅用于算法内部）
* 初始簇成员列表

---

## 9. hierarchical 后端规范

### 9.1 输入

输入向量为：

* 若 `use_pca = true`：`interest_vec_cluster`
* 若 `use_pca = false`：`interest_vec_1024`

### 9.2 核心思想

hierarchical 聚类用于提供一条更接近“自然团块”直觉的路径。
本版本采用“先构建层次结构，再按距离阈值切树”的方式，而不是固定簇数。

### 9.3 参数

新增参数：

* `hierarchical_distance_threshold: float`
* `hierarchical_linkage: str`

合法 linkage 建议：

* `"average"`
* `"complete"`

默认建议：

* `average`

### 9.4 linkage 选择原则

* 不使用 `single`，避免链化问题
* 不优先使用 `ward`，因为当前语义更接近余弦空间而不是方差最小化的欧氏目标
* `average` 作为默认值
* `complete` 可用于得到更紧的簇

### 9.5 距离定义

层次聚类建议使用余弦距离语义。
实现方式可根据库兼容性决定：

* 若 sklearn 版本直接支持所需 metric，则直接使用
* 否则先计算 pairwise cosine distance matrix，再使用 scipy 路线

### 9.6 切簇规则

层次树生成后，根据 `hierarchical_distance_threshold` 切分出最终簇。

该阈值越小，簇越多、越细。
该阈值越大，簇越少、越粗。

### 9.7 输出

hierarchical 输出：

* 每篇文章的簇标签 `labels`
* 初始簇成员列表

---

## 10. 小簇处理

### 10.1 为什么必须做

无论使用哪种算法，都可能产生太小的簇。
太小的簇不利于稳定推荐，也会让簇权重过碎。

因此，小簇处理是统一后处理步骤，必须执行。

### 10.2 定义

若某簇的成员数 `< min_cluster_size`，则该簇视为小簇。

### 10.3 处理规则

1. 统计所有簇大小
2. 将簇分成：

   * 大簇
   * 小簇
3. 若没有任何大簇，则将所有文章合并为一个单簇
4. 若存在大簇，则对每个小簇中的每篇文章：

   * 找到最近的大簇
   * 重新挂到该大簇

### 10.4 最近大簇的距离空间

**注意：最近大簇的判断必须使用原始 1024 维兴趣向量空间。**

实现步骤：

1. 先基于当前分配，用原始 1024 维兴趣向量计算每个大簇的质心
2. 对小簇中的文章，计算它与各大簇质心的距离
3. 分配给最近的大簇

原因：

最终推荐系统使用的是原始 1024 维空间，因此小簇重分配也应尽量在同一语义空间中完成。

---

## 11. 最终质心计算

### 11.1 必须使用原始 1024 维兴趣向量

无论聚类本身发生在哪个空间，最终落库质心一律在原始 1024 维兴趣向量空间中计算。

### 11.2 计算方法

设簇 (C_k) 中包含文章集合 ({i})，其原始 1024 维兴趣向量为 (v_i)，则：

[
c_k = \frac{1}{|C_k|} \sum_{i \in C_k} v_i
]

然后对 (c_k) 做一次 L2 normalization。

### 11.3 质心用途

最终质心用于：

* 存入 `interest_clusters`
* 后续新文章推荐打分
* 小簇重分配时的最近大簇计算

---

## 12. 是否做“近簇再合并”

### 12.1 k-means++ 路径

允许做近簇合并，但建议做成 **可选开关**。

新增参数：

* `enable_post_merge: bool`
* `merge_distance_threshold: float`

处理逻辑：

1. 使用原始 1024 维最终质心
2. 两两计算簇质心距离
3. 距离小于阈值则视为应合并
4. 用并查集合并
5. 合并后重新计算最终质心

### 12.2 hierarchical 路径

默认 **不做额外近簇合并**。

原因：

hierarchical 已经通过距离阈值切树表达了簇的粒度控制。
再叠加一次近簇合并会使阈值语义混乱。

---

## 13. 统一输出结构

定义统一结果对象：

```python
@dataclass
class BuildInterestClustersResult:
    article_ids: list[int]
    labels: np.ndarray
    cluster_members: dict[int, list[int]]
    cluster_centroids_1024: dict[int, np.ndarray]
    cluster_sizes: dict[int, int]
    algo: str
    use_pca: bool
    pca_dim: int | None
    pca_explained_variance: float | None
```

说明：

* `labels` 的顺序必须与 `article_ids` 一一对应
* `cluster_members` 中的成员建议保存为 article index 列表或 article_id 列表，但内部需要统一
* `cluster_centroids_1024` 必须全部是原始 1024 维空间质心

---

## 14. 数据库写入规范

### 14.1 表 `interest_clusters`

每个最终簇写入一条记录，字段包括：

* `id`
* `label`
* `size`
* `summary_centroid` 或当前已有质心字段
* `created_at`
* `updated_at`

### 14.2 表 `interest_cluster_members`

每条簇成员关系写入一条记录，字段包括：

* `cluster_id`
* `article_id`
* `membership`

本版本：

* `membership = 1.0`

### 14.3 表 `interest_meta`

至少更新：

* `interest_clusters_last_built_at`

建议新增以下调试字段：

* `interest_cluster_algo`
* `interest_cluster_use_pca`
* `interest_cluster_pca_variance_threshold`
* `interest_cluster_pca_dim`
* `interest_cluster_tag_weight`

---

## 15. 簇编号规则

算法内部产生的簇标签可能不稳定，因此写库前必须重新编号。

建议规则：

1. 按簇大小从大到小排序
2. 若簇大小相同，则按簇内最小 `article_id` 排序
3. 按排序结果重新编号为 `1..K`

这样可以尽量减少不同重建之间的编号漂移。

---

## 16. CLI / 参数规范

建议支持 CLI 参数，同时允许环境变量作为默认值来源。

### 16.1 核心参数

* `--algo`

  * `kmeans++`
  * `hierarchical`

* `--tag-weight`

  * float
  * 默认 `0.75`

* `--use-pca`

  * bool
  * 默认 `true`

* `--pca-explained-variance-threshold`

  * float
  * 例如 `0.90` / `0.95`

* `--min-cluster-size`

  * int

* `--max-clusters`

  * int
  * 仅对 kmeans++ 有效

### 16.2 kmeans++ 参数

* `--kmeans-random-state`
* `--kmeans-n-init`
* `--kmeans-max-iter`
* `--enable-post-merge`
* `--merge-distance-threshold`

### 16.3 hierarchical 参数

* `--hierarchical-distance-threshold`
* `--hierarchical-linkage`

---

## 17. 日志要求

每次构建必须输出足够日志，方便比较两种算法和 PCA 的效果。

### 17.1 输入统计

* 总文章数
* 同时有两类向量的文章数
* 只有 `summary_vec` 的文章数
* 只有 `tag_vec` 的文章数
* 最终参与聚类文章数

### 17.2 向量统计

* `tag_weight`
* 是否做支路归一化
* 是否做最终归一化
* 若启用调试模式，可输出：

  * `summary_vec` 模长分布摘要
  * `tag_vec` 模长分布摘要
  * 最终向量模长分布摘要

### 17.3 PCA 统计

* 是否启用 PCA
* 原始维度
* 目标累计解释方差阈值
* 自动选择出的维度
* 实际累计解释方差

### 17.4 聚类统计

* 使用算法
* 聚类输入维度
* 原始簇数量
* 小簇数量
* 小簇处理后簇数量
* 是否执行 post-merge
* 最终簇数量
* 最大簇大小
* 最小簇大小
* 中位簇大小

---

## 18. 模块拆分建议

建议按以下模块拆分代码。

### 18.1 `load_articles_for_clustering(...)`

职责：

* 从数据库读取候选文章和 embedding
* 做基础过滤
* 返回原始记录列表

返回：

```python
list[ArticleEmbeddingRecord]
```

### 18.2 `build_interest_vectors(...)`

职责：

* 对每篇文章构造原始 1024 维兴趣向量
* 执行归一化
* 返回：

  * `article_ids`
  * `vectors_1024`

### 18.3 `fit_pca_if_enabled(...)`

职责：

* 若启用 PCA，则根据累计解释方差阈值自动选维
* 生成 `vectors_cluster`
* 返回：

  * `vectors_cluster`
  * `pca_dim`
  * `explained_variance`

### 18.4 `run_kmeans_backend(...)`

职责：

* 基于 `vectors_cluster` 运行 kmeans++
* 返回初始 `labels`

### 18.5 `run_hierarchical_backend(...)`

职责：

* 基于 `vectors_cluster` 运行层次聚类
* 返回初始 `labels`

### 18.6 `reassign_small_clusters(...)`

职责：

* 用原始 1024 维向量执行小簇处理
* 返回修正后的 `labels`

### 18.7 `merge_close_clusters_if_enabled(...)`

职责：

* 仅对 `kmeans++` 路径执行可选近簇合并
* 使用原始 1024 维最终质心
* 返回修正后的 `labels`

### 18.8 `compute_final_centroids_1024(...)`

职责：

* 根据最终 `labels`
* 在原始 1024 维空间中计算最终质心
* 返回：

  * `cluster_members`
  * `cluster_centroids_1024`
  * `cluster_sizes`

### 18.9 `persist_interest_clusters(...)`

职责：

* 写入三张表
* 更新 meta

---

## 19. 推荐系统兼容要求

构建出的兴趣簇必须可直接支持以下推荐流程：

1. 对新文章构造原始 1024 维兴趣向量
2. 与每个簇的原始 1024 维质心计算相似度
3. 按簇权重加权
4. 加总得到总兴趣分

因此，本版本必须保证：

* 所有最终质心都在原始 1024 维空间
* 所有质心已归一化
* 所有文章最终只属于一个簇
* 簇数量不应过碎
* 输出结果尽可能稳定

---

## 20. 建议默认配置

### kmeans++ 默认值

* `algo = kmeans++`
* `tag_weight = 0.75`
* `use_pca = true`
* `pca_explained_variance_threshold = 0.95`
* `min_cluster_size = 8` 或按现有系统默认值
* `max_clusters = 50` 或按现有系统默认值
* `kmeans_random_state = 42`
* `kmeans_n_init = 10`
* `kmeans_max_iter = 300`
* `enable_post_merge = true`

### hierarchical 默认值

* `algo = hierarchical`
* `tag_weight = 0.75`
* `use_pca = true`
* `pca_explained_variance_threshold = 0.95`
* `min_cluster_size = 8` 或按现有系统默认值
* `hierarchical_linkage = average`
* `hierarchical_distance_threshold = 需要通过实验确定`

---

## 21. 推荐实现顺序

### 第一步：完成统一数据准备层

实现：

* 数据读取
* 兴趣向量构造
* L2 归一化
* PCA 自动选维

并输出：

* `article_ids`
* `vectors_1024`
* `vectors_cluster`

先保证这一层独立可测试。

### 第二步：实现 kmeans++ 后端

实现：

* `k0` 计算
* `kmeans++`
* 小簇处理
* 可选近簇合并
* 最终质心重算
* 写库

先让它完整替代旧实现。

### 第三步：实现 hierarchical 后端

实现：

* 距离矩阵或直接层次聚类
* 距离阈值切簇
* 小簇处理
* 最终质心重算
* 写库

### 第四步：统一 CLI 与日志

确保：

* 两种算法可切换
* PCA 参数可切换
* 构建日志完整

---

## 22. 验收标准

### 功能验收

* 可以通过参数切换 `kmeans++` 和 `hierarchical`
* 可以启用或关闭 PCA
* PCA 维度通过累计解释方差自动确定
* 两种算法都能正确写库
* 输出结果可直接用于现有推荐流程

### 结果验收

* 不再依赖旧的顺序初始化逻辑
* 最终质心全部为原始 1024 维
* 聚类结果稳定可复现
* 小簇被合理处理
* 簇数量和簇大小分布可接受

### 工程验收

* 数据准备层与算法层分离
* 小簇处理逻辑统一
* 写库逻辑统一
* 日志足够支持后续调参与算法对比

---

## 23. 最后结论

本版本的核心不是“多加两种算法”这么简单，而是建立一个统一的兴趣簇构建框架：

* 同一套兴趣向量
* 同一套 PCA 规则
* 两种可切换聚类后端
* 同一套小簇处理
* 同一套最终质心重算
* 同一套写库与推荐兼容输出

其中最重要的硬约束是：

**聚类可以在 PCA 空间进行，但最终落库的簇质心必须在原始 1024 维兴趣向量空间重新计算。**

这条规则是整个系统和后续推荐兼容的关键。

如果你愿意，我下一条可以继续把这个 SPEC 直接扩成一个 **面向实现的任务拆解清单**，比如拆成 10 到 15 个可提交的小任务，每个任务写出输入、输出、完成标准。
