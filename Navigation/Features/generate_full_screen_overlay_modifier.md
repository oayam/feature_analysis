# 1. 简介

arkui_ace_engine是openharmony的ui引擎（在openharmony的目录：`foundation/arkui/ace_engine`），其中包含多种前后端框架，例如：

* arkts的js属性方法构成的前端（解析的入口：`arkui_ace_engine/frameworks/bridge/declarative_frontend/jsview/`）、cpp构成的后端。前端示例：

  ```
  Navigation() {
  
  }
  .hideTitleBar(true) // this `.hideTitileBar` is a attribute of component `Navigation`
  ```

* js属性对应的modifier前端（解析的入口：`arkui_ace_engine/frameworks/bridge/declarative_frontend/ark_component`）、cpp构成的后端

  > 参考文档：https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/arkts-user-defined-extension-attributemodifier

理论上来说，如上的两种前后端框架逻辑一致、共用后端，仅前端解析层有实现差异。因此，可以根据js属性方法框架的实现推倒出对应的modifier框架的实现。

# 2. 穿刺实现

当前库上代码已经实现了`NavDestination`组件`fullScreenOverlay`属性的js属性实现。请参照章节1所述，自行搜索、学习并参照对应目录的代码实现，实现`fullScreenOverlay`属性对应的modifier解析逻辑

# 3. 总结skill

> 暂时无需关注