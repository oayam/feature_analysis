# base

请先完成如下前置学习

- [ ] 请搜索navigation组件相关的实现（主要了解navigation从js侧到cpp侧的前后端解析与组件的布局逻辑）
- [ ] 阅读navigation组件mode属性的实现（主要包括参数解析、枚举以及对应的布局效果）

阅读理解完成后，请帮我完成需求，该需求会为navigation的mode枚举增加一个类型（当前枚举有如下类型：stack、split、auto），名称为AUTO_WITH_RATIO（代码实现时请根据所处上下文动态修改命名格式，例如在js侧命名格式为带下划线的全大写，在cpp侧为小驼峰命名）。

该枚举的行为如下

1. 当navigation组件的实际布局高度 / 实际布局宽度 > 1.2时，navigation采用stack模式布局
2. 当navigation组件的实际布局高度 / 实际布局宽度 <= 1.2时，navigation采用split模式布局

# 新增1

请完成如下学习：

- [ ] openharmony arkui中navigation组件的modifier框架（核心文件：`./frameworks/core/interfaces/native/node/navigation_modifier.cpp`）
- [ ] 自行搜索、学习navigation的modifier是如何运行、如何对接到后端框架的（后端框架核心文件：`./frameworks/core/components_ng/pattern/navigation/navigation_model_ng.h`）

学习完毕后，请将base章节中新增的枚举按照modifier的格式进行实现，并生成对应的代码
