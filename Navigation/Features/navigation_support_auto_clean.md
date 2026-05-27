# Navigation 自动清理路由栈

## 〇、前置知识

请学习[Navigation架构介绍](../Navigation_intro.md)了解navigation组件

## 一、需求概述

当路由页面的数量大于开发者设置的最大路由数量时，根据index从小到大的顺序自动清理页面

### 应用场景

- 控制低端设备（例如内存仅有4G）应用内存

---

## 二、核心设计原则

1. 全局配置：Navigation提供API配置栈大小限制。
2. 默认行为：超出限制时自动清理，无需开发者控制。
3. 仅清理不可见：考虑到透明的dialog类型页面，仅清理当下不可见的页面。清理页面时，走完整的销毁生命周期流程。
4. 自动恢复：当被清理的页面再次可见时，走完整的创建生命周期流程。
5. 状态管理：提供onSaveState/onRestoreState回调接口用于保存、恢复状态。
6. 职责分离：Navigation负责配置栈大小，NavDestination负责状态保存/恢复

## 三、API

1. NavigationConfiguration接口

文件 `interface/sdk-js/api/@internal/component/ets/navigation.d.ts`

```ts
/**
 * Navigation configuration options.
 * 
 * @interface NavigationConfiguration
 * @syscap SystemCapability.ArkUI.ArkUI.Full
 * @stagemodeonly
 * @crossplatform
 * @atomicservice
 * @since 26.0.0 dynamic
 */
declare interface NavigationConfiguration {
 /**
  * Navigation page stack size limit.
  *
  * Description:
  * - Limits to maximum number of active page nodes in Navigation page stack.
  * - When limit is exceeded, oldest page nodes are automatically destroyed
  *   in FIFO (First-In-First-Out) order.
  * - NavPathInfo of pages is completely retained, supporting page recreation.
  * - value <=0 No limit on page stack size (default value).
  * - value >0 Limit stack size to specified value.
  *
  * @type { ?int }
  * @default 0 (no limit)
  * @syscap SystemCapability.ArkUI.ArkUI.Full
  * @stagemodelonly
  * @crossplatform
  * @atomicservice
  * @since 26.0.0 dynamic
  */
 stackSizeLimit?: int;
}
```

```ts
/**
 * Sets Navigation configuration.
 *
 * @param { NavigationConfiguration } config - Navigation configuration options.
 * @returns { NavigationAttribute } Returns instance of NavigationAttribute.
 * @syscap SystemCapability.ArkUI.ArkUI.Full
 * @stagemodelonly
 * @crossplatform
 * @atomicservice
 * @since 26.0.0 dynamic
 */
configuration(config: NavigationConfiguration): NavigationAttribute;
```

2. onSaveState/onRestoreState回调接口

```ts
declare type OnSaveStateCallback = () => Record<string, ESObject> | undefined;
declare type OnRestoreStateCallback = (Record<string, ESObject> | undefined) => void;
```

```ts
/**
 * Called when the navigation destination page will be cleaned.
 *
 * @param { OnSaveStateCallback } callback - callback to save states of current component.
 * @returns { NavDestinationAttribute }
 * @syscap SystemCapability.ArkUI.ArkUI.Full
 * @stagemodelonly
 * @crossplatform
 * @atomicservice
 * @since 26.0.0 dynamic
 */
onSaveState(callback: OnSaveStateCallback): NavDestinationAttribute;
```

```ts
/**
 * Called when the navigation destination page will be restored.
 *
 * @param { OnRestoreStateCallback } callback - callback to restore states of current component.
 * @returns { NavDestinationAttribute }
 * @syscap SystemCapability.ArkUI.ArkUI.Full
 * @stagemodelonly
 * @crossplatform
 * @atomicservice
 * @since 26.0.0 dynamic
 */
onRestoreState(callback: OnRestoreStateCallback): NavDestinationAttribute;
```

## 四、实现

### 4.1 基础解析、声明

使用skill`SDK to base-impl`生成

### 4.2 后端逻辑调用

栈同步后，如果`(config.limit > 0 && config.limit < stackSize) || configLimitUpdated`：直接操作navPathList，并更新configLimitUpdated为false

> configLimitUpdated在pattern的config更新时更新。

int32_t restoreMinIndex = MAX(0, MIN(lastStandardIndex , stackSize - config.limit))

restore：

* 从restoreMinIndex 开始正向遍历navPathList，对于每一个元素：
  
  * 如果节点为nullptr，创建节点并标记对应的jsNavPathInfo的autoCleaned为undefined（并触发onRestoreState）；continue；

  * 如果节点pattern上的标志位pendingToClean_ = true，更新该标志位为false；continue
  
  * 否则什么都不做

clean：

* 从restoreMinIndex 开始逆向遍历navPathList，对于每一个元素：

  * 如果节点为nullptr且对应的jsNavPathInfo已经标记了autoCleaned：continue；

  * 如果当前节点是remainChild或isOnAnimation = true：更新位于节点pattern上的标志位pendingToClean_ = true，并在动画结束的回调中根据标志位清理该标志位；continue；

  * 否则需要立刻清理该节点，将navPathList中的node设置为nullptr，将对应的jsNavPathInfo标记为autoCleaned
