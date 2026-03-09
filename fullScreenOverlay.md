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

### 3.0 API类型说明

OpenHarmony ArkUI提供两种类型的API：

| API类型     | 说明                                   | 文件位置                                        | 版本标记            |
| ----------- | -------------------------------------- | ----------------------------------------------- | ------------------- |
| **动态API** | 运行时动态绑定，通过JS引擎调用         | `interface/sdk-js/api/@internal/component/ets/` | `@since 26 dynamic` |
| **静态API** | 编译时静态分析，通过arkui-xp编译器优化 | `interface/sdk-js/api/arkui/component/`         | `@since 26 static`  |

**设计原则**：
- 动态API和静态API提供相同的功能，参数和返回值保持一致
- 静态API支持`undefined`参数以提供更好的类型推断
- 开发者可根据使用场景选择合适的API类型

---

### 3.1 命令式指定（方案一：单次跳转生效）

#### 3.1.1 动态API - 扩展NavPathInfo接口

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
  fullScreen?: boolean;
}
```

**使用示例**：
```typescript
// 通过pushPath指定
this.pageStack.pushPath({
  name: 'FullScreenPage',
  param: { data: 'test' },
  fullScreen: true  // 本次跳转为全屏模式
});

// 普通跳转不受影响
this.pageStack.pushPath({
  name: 'NormalPage',
  param: 'data'
  // fullScreen默认为false
});
```

#### 3.1.2 静态API - 扩展NavPathInfo接口

**文件位置**：`interface/sdk-js/api/arkui/component/navigation.static.d.ets`

```typescript
declare class NavPathInfo {
  /**
   * Page name, which is the name of the registered page.
   *
   * @type { string }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10 static
   */
  name: string;

  /**
   * Parameters passed to the page.
   *
   * @type { ESObject }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10 static
   */
  param: ESObject;

  /**
   * Whether to display the page in full screen overlay mode.
   *
   * In split navigation mode, a full-screen page covers the entire navigation container,
   * overlaying both the nav bar and content area.
   *
   * This setting only applies to this specific navigation operation.
   *
   * @type { boolean | undefined }
   * @default false
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @crossplatform
   * @atomicservice
   * @since 26 static
   */
  get fullScreen(): boolean | undefined;
  set fullScreen(fullScreen: boolean | undefined);
}
```

**与动态API的区别**：
- 参数类型使用 `ESObject` 代替 `unknown`
- `fullScreen` 属性使用 getter/setter 定义
- 支持显式 `undefined` 类型以提供更好的类型推断

---

### 3.2 声明式指定（方案二：页面全局生效）

#### 3.2.1 动态API - NavDestination属性方法

**文件位置**：`interface/sdk-js/api/@internal/component/ets/nav_destination.d.ts`

```typescript
declare class NavPathStack {
  // === 现有方法保持不变 ===

  /**
   * Pushes a page by name with the specified parameter.
   *
   * @param { string } name - Page name.
   * @param { unknown } param - Parameters passed to the page.
   * @param { () => void } [onPop] - Callback invoked when the page is popped.
   * @param { AnimatedValue } [animated] - Whether to play the page transition animation.
   * @returns { void }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10
   */
  pushPathByName(name: string, param: unknown,
    onPop?: () => void, animated?: AnimatedValue): void;

  /**
   * Pushes a page with path info.
   *
   * @param { NavPathInfo } info - Information about the navigation destination page.
   * @param { () => void } [onPop] - Callback invoked when the page is popped.
   * @param { AnimatedValue } [animated] - Whether to play the page transition animation.
   * @returns { void }
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @crossplatform
   * @atomicservice
   * @since 26
   */
  pushPath(info: NavPathInfo,
    onPop?: () => void,
    animated?: AnimatedValue): void;
}
```

**使用示例**：
```typescript
// 使用pushPath方法指定fullScreen
this.pageStack.pushPath({
  name: 'FullScreenPage',
  param: { data: 'test' },
  fullScreen: true
});

// 普通跳转（不设置fullScreen）
this.pageStack.pushPath({
  name: 'NormalPage',
  param: 'data'
});
```

---

### 3.2 声明式指定（方案二：页面全局生效）

#### 3.2.1 动态API - NavDestination属性方法

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

        Text('此页面覆盖左右分栏')
          .fontSize(16)
          .margin({ top: 20 })

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

#### 3.2.2 静态API - NavDestination属性方法

**文件位置**：`interface/sdk-js/api/arkui/component/navDestination.static.d.ets`

```typescript
declare class NavDestinationAttribute {
  /**
   * Sets the page title.
   *
   * @param { string | CustomBuilder | Resource } value - Title text.
   * @returns { NavDestinationAttribute } The matched NavDestinationAttribute.
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10 static
   */
  title(value: string | CustomBuilder | Resource): NavDestinationAttribute;

  /**
   * Specifies whether to hide the title bar.
   *
   * @param { boolean | undefined } value - Whether to hide title bar.
   * @returns { NavDestinationAttribute } The matched NavDestinationAttribute.
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @since 10 static
   */
  hideTitleBar(value: boolean | undefined): NavDestinationAttribute;

  // === 新增属性 ===

  /**
   * Sets whether the NavDestination should cover the entire navigation container.
   *
   * When set to true, in split navigation mode, the page covers both the nav bar
   * and content area, displaying in full screen overlay mode. This setting applies
   * to all instances of this NavDestination whenever it is pushed onto the stack, unless
   * overridden by the fullScreen option in the push operation.
   *
   * @param { boolean | undefined } fullScreenOverlay - Whether to display as full screen overlay.
   * <br>**true**: Full screen overlay mode, covers entire navigation container.
   * <br>**false**: Normal display mode, follows navigation split rules.
   * <br>**undefined**: Set to default value (false).
   * @returns { this } The matched NavDestinationAttribute.
   * @syscap SystemCapability.ArkUI.ArkUI.Full
   * @crossplatform
   * @atomicservice
   * @since 26 static
   */
  default fullScreenOverlay(fullScreenOverlay: boolean | undefined): this;
}
```

**使用示例（静态API）**：
```typescript
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
      .justifyContent(FlexAlign.Center)
    }
    .fullScreenOverlay(true)  // 静态API：链式调用返回this
    .title('全屏页面')
  }
}
```

---

## 四、动态API与静态API对比

| 特性              | 动态API                    | 静态API                 |
| ----------------- | -------------------------- | ----------------------- |
| **绑定时机**      | 运行时动态绑定             | 编译时静态分析          |
| **类型检查**      | 运行时检查                 | 编译时严格检查          |
| **性能**          | 灵活但开销较大             | 高性能，编译器优化      |
| **类型推断**      | 基于 `unknown`             | 基于 `ESObject`，更精确 |
| **参数undefined** | 不支持                     | 显式支持，有默认值语义  |
| **适用场景**      | 动态构建UI、热更新         | 静态页面、性能关键场景  |
| **文件位置**      | `@internal/component/ets/` | `arkui/component/`      |
| **版本标记**      | `@since 26 dynamic`        | `@since 26 static`      |

**API选择建议**：
- 推荐使用**静态API**以获得更好的性能和类型检查
- 需要动态构建UI的场景使用**动态API**

---

## 五、显示规则

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

---