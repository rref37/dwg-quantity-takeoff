# DDC DwgExporter 导出 Excel 的结构

DwgExporter 把 DWG 每个对象/实体导成一行,列有约 1000 个(各实体类型的属性全摊平在一张表)。第一个 sheet 是数据,后面 `Projects`/`Ads_DDC` 可忽略。

## 必懂的关键列

| 列名 | 含义 / 坑 |
|---|---|
| `Description` | 实体类型,带尖括号:`<AcDbBlockReference>`(块引用)、`<AcDbText>`/`<AcDbMText>`(文字)、`<AcDbAttribute>`(块属性)、`<AcDbLine>`/`<AcDbArc>`/`<AcDbCircle>`/`<AcDbPolyline>`(几何)、`<AcDbBlockTableRecord>`(块定义)、`<AcDbViewport>`(图框视口) |
| `BlockTableRecord` | **块引用实例化的真实块名**。统计图块就用这列。⚠️ 不要用 `Name` 列——`Name` 对块引用恒为字符串 "BlockReference",没用 |
| `BlockId` | 该实体所属的容器:`*Model_Space` / `*Paper_Space` / 某个块定义名。**用它把一个块定义内部的子几何聚起来做指纹**(方法②) |
| `Layer` | 图层名。各专业最稳的分类维度 |
| `Position` | 块引用/文字的插入点,字符串 `"x, y, z"` |
| `Center` `Radius` | 圆/弧的圆心、半径 |
| `StartAngle` `EndAngle` | 弧的起止角(弧度) |
| `StartPoint` `EndPoint` | 线的端点 |
| `ViewCenter` `ViewHeight` | 视口显示的模型区中心点 + 模型高度(分栋/去重关键) |
| `Width` `Height` | 视口在图纸上的纸面尺寸(算模型宽度用:模型宽 = ViewHeight × 纸面Width/纸面Height) |
| `Number` | 视口编号;`1` 是图纸纸张本身,跳过 |

## 解析坐标

坐标列都是 `"199.999, 200.001, 0"` 形式的字符串。用正则取前两个数即可(见 `_common.py` 的 `xy()`)。

## 指纹(方法②)怎么算

1. 按 `BlockId` 把所有 `<AcDb...>` 几何行分组(每组 = 一个块定义的内部构成)。
2. 每组统计各几何类型的个数,排序成元组,如 `(('Arc',16),('Circle',1),('Line',4))` = 该块的几何指纹。
3. 块引用通过 `BlockTableRecord` 知道自己是哪个定义 → 查指纹。相同指纹 = 同一符号。

## 完整性自检

把 9 个(或 N 个)文件的总行数、块数列个表(本技能成品里的"图层原始统计"页就是干这个)。行数明显偏少 = 那个文件没爬全。各栋同名平面文件块数几乎相同 = 共用模型空间。
