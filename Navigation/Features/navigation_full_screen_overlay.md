# Navigation 全屏覆盖页面设计方案

## 一、需求概述

在Navigation分栏模式下，支持NavDestination页面通过push入栈后全屏显示，覆盖整个Navigation容器（包括左侧NavBar和右侧内容区）。

### 应用场景

- 重要表单页面需要全屏填写
- 详情页面需要展示更多内容
- 特殊业务流程页面需要用户专注操作
- 模态交互场景

---

## 二、核心设计原则

1. **双模式支持**：同时支持命令式（单次跳转）和声明式（页面级）两种指定方式
2. **向后兼容**：不影响现有代码，默认行为不变
3. **规则清晰**：嵌套场景的显示行为明确定义
4. **Dialog兼容**：与Dialog模式互不冲突，可组合使用
5. **自动升级**：全屏页面之后的页面自动升级为全屏显示

---

## 三、接口设计

### 3.1 命令式指定（方案一：单次跳转生效）

#### 3.1.1 扩展NavPathInfo接口

**文件位置**：`interface/sdk-js/api/@internal/component/ets/navigation.d.ts`

```typescript
declare interface NavPathInfo {
  /**
   * Page name, which is the name of the registered page.
   *
   * @type { string }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10
   */
  name: string;

  /**
   * Parameters passed to the page.
   *
   * @type { unknown }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10
   */
  param: unknown;

  /**
   * Whether to display the page in full screen overlay mode.
   * In split navigation mode, a full-screen page covers the entire navigation container,
   * overlaying both the nav bar and content area.
   *
   * This setting only applies to this specific navigation operation.
   *
   * @type { boolean }
   * @default false
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @crossplatform
   * @atomicservice
   * @since 26
   */
  fullScreenOverlay?: boolean;
}
```

**使用示例**：
```typescript
// 通过pushPath指定
this.pageStack.pushPath({
  name: 'FullScreenPage',
  param: { data: 'test' },
  fullScreenOverlay: true  // 本次跳转为全屏模式
});

// 普通跳转不受影响
this.pageStack.pushPath({
  name: 'NormalPage',
  param: 'data'
  // fullScreenOverlay默认为false
});
```

### 3.2 声明式指定（方案二：页面全局生效）

#### 3.2.1 NavDestination属性方法

**文件位置**：`interface/sdk-js/api/@internal/component/ets/nav_destination.d.ts`

```typescript
declare class NavDestinationAttribute extends CommonMethod<NavDestinationAttribute> {
  // === 现有属性 ===

  /**
   * Sets the page title.
   *
   * @param { string | CustomBuilder | NavDestinationCommonTitle | NavDestinationCustomTitle | Resource } value
   * @param { NavigationTitleOptions } [options] - Indicates the options of titlebar.
   * @returns { NavDestinationAttribute }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 14
   */
  title(value: string | CustomBuilder | NavDestinationCommonTitle | NavDestinationCustomTitle | Resource,
    options?: NavigationTitleOptions): NavDestinationAttribute;

  /**
   * Specifies whether to hide the title bar.
   *
   * @param { boolean } value
   * @returns { NavDestinationAttribute }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 9
   */
  hideTitleBar(value: boolean): NavDestinationAttribute;

  // === 新增属性 ===

  /**
   * Sets whether the NavDestination should cover the entire navigation container.
   *
   * When set to true, in split navigation mode, the page covers both the nav bar
   * and content area, displaying in full screen overlay mode. This setting applies
   * to all instances of this NavDestination whenever it is pushed onto the stack.
   *
   * @param { boolean } fullScreenOverlay - Whether to display as full screen overlay.
   * <br>**true**: Full screen overlay mode, covers entire navigation container.
   * <br>**false**: Normal display mode, follows navigation split rules.
   * @returns { NavDestinationAttribute }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @crossplatform
   * @atomicservice
   * @since 26
   */
  fullScreenOverlay(fullScreenOverlay: boolean): NavDestinationAttribute;
}
```

**使用示例**：
```typescript
@Builder
export function FullScreenPageBuilder(name: string, param: string) {
  FullScreenPage({ name: name, value: param });
}

@Component
export struct FullScreenPage {
  build() {
    NavDestination() {
      Column() {
        Text('全屏覆盖页面')
          .fontSize(28)
          .fontWeight(FontWeight.Bold)

        Button('返回')
          .margin({ top: 40 })
          .onClick(() => {
            this.pageStack.pop();
          })
      }
      .width('100%')
      .height('100%')
      .backgroundColor(Color.White)
      .justifyContent(FlexAlign.Center)
    }
    .fullScreenOverlay(true)  // 声明式：此页面始终全屏显示
    .title('全屏页面')
  }
}

// 跳转时正常push即可
this.pageStack.pushPathByName('FullScreenPage', 'param');
```

---

## 四、显示规则

### 4.1 基本规则

| 显示模式         | 说明                                                     |
| ---------------- | -------------------------------------------------------- |
| **分栏模式**     | 左侧NavBar固定，右侧显示NavDestination内容区             |
| **全屏覆盖模式** | NavDestination覆盖整个Navigation容器，包括NavBar和内容区 |

### 4.2 全屏判断规则

一个页面的最终显示状态由以下因素决定（优先级从高到低）：

1. **栈继承规则**：如果栈中存在全屏页面，且当前页面在其之上，则自动升级为全屏
2. **命令式指定**：`NavPathInfo.fullScreen`
3. **声明式指定**：`.fullScreenOverlay()` 属性

**判断逻辑**：
```typescript
function shouldDisplayFullScreen(pageName: string, stackIndex: number): boolean {
  // 1. 检查栈继承规则
  const topFullScreenIndex = findTopFullScreenPageIndex();
  if (topFullScreenIndex !== -1 && stackIndex > topFullScreenIndex) {
    return true;  // 在全屏页面之后，自动升级
  }

  // 2. 检查命令式指定（本次跳转的fullScreen参数）
  if (currentPushInfo.fullScreen === true) {
    return true;
  }

  // 3. 检查声明式指定（页面的fullScreenOverlay属性）
  if (pageDefinition.fullScreenOverlay === true) {
    return true;
  }

  return false;
}
```

### 4.3 嵌套场景示例

#### 场景1：分栏 → 全屏页面

```
初始状态：分栏模式
┌──────────┬─────────────────────────┐
│  NavBar  │    Page A               │
│  (固定)  │    (普通页面)            │
│          │                         │
└──────────┴─────────────────────────┘

执行：this.pageStack.pushPath({ name: 'PageB', fullScreen: true })

结果：
┌─────────────────────────────────────────┐
│      Page B (fullScreen: true)          │
│      覆盖整个Navigation容器              │
│                                         │
└─────────────────────────────────────────┘
```

#### 场景2：全屏页面 → 普通页面（自动升级）

```
当前状态：
┌─────────────────────────────────────────┐
│      Page B (fullScreen: true)          │
│      栈顶全屏页面                        │
└─────────────────────────────────────────┘

执行：this.pageStack.pushPathByName('PageC', 'param')
      注意：PageC未设置fullScreen

结果：
┌─────────────────────────────────────────┐
│      Page C (自动升级为全屏)              │
│      虽未设置fullScreen，但自动全屏显示    │
└─────────────────────────────────────────┘

栈状态：[PageA, PageB(全屏), PageC(自动全屏)]
```

#### 场景3：多层嵌套后返回

```
当前状态：
栈：[PageA, PageB(全屏), PageC(自动全屏), PageD(自动全屏)]

执行：this.pageStack.pop()

结果：
栈：[PageA, PageB(全屏), PageC(自动全屏)]
显示：PageC 全屏显示

执行：this.pageStack.pop()

结果：
栈：[PageA, PageB(全屏)]
显示：PageB 全屏显示

执行：this.pageStack.pop()

结果：
栈：[PageA]
显示：PageA 分栏显示（恢复NavBar和内容区）
```

### 4.4 与Dialog模式的组合

| 组合方式                               | 效果                                 |
| -------------------------------------- | ------------------------------------ |
| `fullScreen: false` + `mode: STANDARD` | 普通页面，分栏模式下显示在右侧内容区 |
| `fullScreen: false` + `mode: DIALOG`   | 透明弹窗，分栏模式下显示在右侧内容区 |
| `fullScreen: true` + `mode: STANDARD`  | 全屏覆盖页面                         |
| `fullScreen: true` + `mode: DIALOG`    | 全屏透明弹窗，覆盖整个Navigation容器 |

**示例**：
```typescript
// 全屏透明弹窗
NavDestination() {
  // ...
}
.mode(NavDestinationMode.DIALOG)
.fullScreenOverlay(true)
.backgroundColor('rgba(0, 0, 0, 0.5)')
```

### 4.5 动画模式

#### 4.5.1 分栏显示跳转到全屏覆盖页面

┌──────────┬─────────────────────────┐
│  NavBar  │    Page A               │
│  (固定)  │    (普通页面)            │
│          │                         │
└──────────┴─────────────────────────┘
-->>
┌────────────────────────────────────┐
│      Page B (fullScreen: true)     │
│      栈顶全屏页面                   │
└────────────────────────────────────┘
NavBar和Page A不动，Page B做SLIDE_RIGHT的动画（也就是NavDestination的systemTransition属性中的SLIDE_RIGHT），从屏幕外（右侧，如果是RTL则是左侧）平移屏幕内，最终全屏显示。

> 注意！！新进场的全屏页面，不会破坏已有的分栏效果！！也就是NavBar和Page A仍然保持分栏布局，只是被Page B遮挡。


#### 4.5.2 全屏覆盖页面返回分栏显示

┌────────────────────────────────────┐
│      Page B (fullScreen: true)     │
│      栈顶全屏页面                   │
└────────────────────────────────────┘
-->>
┌──────────┬─────────────────────────┐
│  NavBar  │    Page A               │
│  (固定)  │    (普通页面)            │
│          │                         │
└──────────┴─────────────────────────┘
NavBar和Page A不动，Page B做SLIDE_RIGHT的动画（也就是NavDestination的systemTransition属性中的SLIDE_RIGHT），从屏幕中平移屏幕外（屏幕右侧，如果是RTL则是左侧）。

#### 4.5.3 全屏覆盖页面之间相互跳转

┌────────────────────────────────────┐
│      Page A (fullScreen: true)     │
│      栈顶全屏页面                   │
└────────────────────────────────────┘
<<-->>
┌────────────────────────────────────┐
│      Page B (fullScreen: true)     │
│      栈顶全屏页面                   │
└────────────────────────────────────┘
Page A跳转至新页面Page B时：Page A不动，Page B做SLIDE_RIGHT的动画（也就是NavDestination的systemTransition属性中的SLIDE_RIGHT），从屏幕外（右侧，如果是RTL则是左侧）平移屏幕内，最终全屏显示。
Page B返回至Page A页面时：Page B做SLIDE_RIGHT的动画（也就是NavDestination的systemTransition属性中的SLIDE_RIGHT），从屏幕中平移屏幕外（屏幕右侧，如果是RTL则是左侧）。

---
## 五、实现要点

### 5.1 navigation架构

请参考[navigation架构文档](../feature_analysis/Navigation/Navigation_intro.md)进行代码开发，请保证代码符合架构设计

### 5.2 注意事项

1. 本能力整体为新增能力，不要复用代码中已有的全屏显示能力（例如：IsTopFullScreenPage以及相关的链路）。同时，命名要注意区分开。
2. 由于fullScreenOverlay类型的页面需要全屏显示，且不破坏下层的分栏显示，因此navigation组件需要一个专属的层级来挂载这些节点（如果全屏页面挂载在navigationContent节点下，全屏页面布局时会受到父组件navigationContent的限制，进而导致无法全屏），请新增。

---

## 十、实现架构

### 10.1 总体分层

本需求按“接口透传 -> 状态决策 -> 节点挂载 -> 布局测量 -> 可见性与动画”五层落地：

1. **接口透传层**
   - 命令式入口使用 `NavPathInfo.fullScreenOverlay`。
   - 声明式入口使用 `NavDestination.fullScreenOverlay(true)`。
   - JS/ArkTS Bridge、Native Modifier、NG Model 三条链路统一汇总到 `NavDestinationLayoutPropertyBase::FullScreenOverlay` 与 `NavPathInfo::fullScreenOverlay_`。

2. **状态决策层**
   - `NavigationGroupNode::UpdateLastStandardIndex()` 顺序扫描栈内页面。
   - 页面是否进入 overlay 由两部分共同决定：
     - 页面自身显式请求：`HasFullScreenOverlayRequest()`
     - 栈继承规则：一旦某个页面生效为 overlay，其上的页面自动继承
   - 决策结果写入 `NavDestinationGroupNode::isFullScreenOverlay_`，作为后续挂载、布局、显隐、动画的统一依据。

3. **节点挂载层**
   - `NavigationGroupNode` 新增独立子容器 `overlayNode_`，tag 为 `NavigationFullScreenOverlay`。
   - Navigation 内部形成两条并行挂载通道：
     - `contentNode_`：承载普通分栏页面
     - `overlayNode_`：承载全屏覆盖页面
   - `ReorderNavDestination()` 根据 `IsFullScreenOverlay()` 将页面分流到不同容器，并支持节点在两容器间重挂载。

4. **布局测量层**
   - `NavigationLayoutAlgorithm` 对 `overlayNode_` 按整个 Navigation 容器尺寸进行 measure/layout。
   - 因为 overlay 页面不再挂在 `navigationContent` 下，所以不会受右侧内容区宽度限制，可直接覆盖 NavBar 与内容区。

5. **可见性与动画层**
   - `UpdateNavDestinationVisibility()` 分别基于 content/overlay 两套 top index 与 last standard index 处理显隐。
   - 普通 push/pop、dialog push/pop、soft transition 均增加 overlay 分支：
     - overlay push：底层 NavBar/内容区不参与位移动画，仅新页面入场
     - overlay pop：底层页面不参与回场动画，仅 overlay 页面退场
   - 这样可以保证“下层 split 布局保持原样，只被 overlay 页面遮挡”。

### 10.2 关键数据结构

为支持 content 与 overlay 两套栈内可见区间，`NavigationGroupNode` 新增以下索引：

- `contentLastStandardIndex_`：普通内容容器中的最后一个标准页
- `overlayStartIndex_`：首个 overlay 页面在导航栈中的位置
- `overlayLastStandardIndex_`：overlay 容器中的最后一个标准页
- `preContentLastStandardIndex_` / `preOverlayLastStandardIndex_`：上一帧索引快照，用于转场与显隐比对

这些索引与原有 `lastStandardIndex_` 一起，负责支撑：

- overlay 继承判定
- content/overlay 双容器的顶部页面计算
- dialog/standard 混合场景下的动画节点筛选

### 10.3 主要代码落点

- **接口与属性**
  - `navdestination_model_*`
  - `navigation_model_*`
  - `js_navdestination.*`
  - `js_nav_path_stack.cpp`
  - `js_navigation_stack.*`
  - `arkComponent.js`
  - `arkts_native_nav_destination_bridge.*`
  - `nav_destination_modifier.cpp`

- **运行时节点与布局**
  - `navigation_group_node.*`
  - `navigation_layout_algorithm.cpp`
  - `navdestination_group_node.*`
  - `navdestination_layout_property_base.h`

- **调试与观测**
  - Inspector 输出增加 `fullScreenOverlay`
  - `observer_handler.cpp` 识别 overlay 容器父节点

### 10.4 架构收益

该实现与已有 `IsTopFullScreenPage` 链路完全解耦，具备以下特性：

- 不影响历史分栏/全屏逻辑，默认行为保持不变
- overlay 页面具备独立布局层级，避免破坏底层 split 结构
- 命令式与声明式能力复用同一套运行时状态机
- 标准页、dialog 页、soft transition 均可复用统一的 overlay 判定结果
