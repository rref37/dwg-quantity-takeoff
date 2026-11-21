# 退路:AutoCAD COM 自动化(没有 DwgExporter 时)

DDC DwgExporter 和 AutoCAD 都是第三方软件。本仓库不附带它们，MIT 也不提供它们的许可。DwgExporter 这条旧路线不要求本机同时安装 AutoCAD，但程序本身需要你自行取得授权。只有拿不到它，或要做它给不了的事（读特定属性、改图），才退回 COM 驱动本机已经授权的 AutoCAD。COM 坑很多，按下面来。

## 连接
- `win32com.client.GetActiveObject(...)` 本机常失败(ROT 未注册)。改用 `win32com.client.Dispatch("AutoCAD.Application.25")`(版本号按装的版本,Electrical 2025 = `.25`),它能连上正在运行的实例或启动新实例。
- 连接前若 AutoCAD 没开,先 `Start-Process acad.exe`,**等主窗口就绪**再 Dispatch,否则报 "server execution failed"。
- 反复开关多个图后 AutoCAD 可能崩,Dispatch 会失败 → 重启 acad 再连。

## RPC_E_CALL_REJECTED (-2147418111 "被呼叫方拒绝接收呼叫")
打开文档后 AutoCAD 没就绪会拒绝后续自动化调用。解法:
- 打开后轮询 `app.GetAcadState().IsQuiescent` 直到 True;
- 给**每个** COM 调用套 retry,遇到该错误 sleep 0.25s 重试(可重试错误码:-2147418111 拒收、-2147417851 服务器异常、-2147417846 服务器忙)。

## 模态弹窗卡死
`acconnectwebservices.arx ARX 命令中发生异常` 等弹窗会阻塞 COM。解法:后台线程用 ctypes `EnumWindows` + `SendMessageW(hwnd, WM_CLOSE, 0, 0)` 持续关掉标题含 `arx/异常/exception/acconnect` 的窗口(排除主窗口标题)。

## PaperSpace / 视口
- 材料表/图例/系统图 BOM 常在 **PaperSpace 布局**里,不在 ModelSpace → 同时遍历 `doc.Layouts[].Block`。
- 视口的模型范围:`AcadPViewport.Target` COM 里**常返回 (0,0,0) 不可靠**。要分栋/去重,优先改用 DwgExporter 导出的 `ViewCenter`/`ViewHeight` 列。

## 提点坐标
点坐标用 `win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [x,y,z])` 传。

## 块名
块引用真实名用 `EffectiveName`(动态块解析后的名);仍返回 `A$C...` 的是真匿名块(数组/炸开),只能靠几何指纹(方法②)。
