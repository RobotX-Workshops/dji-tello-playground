# 🎮 Controllers and Joysticks

This page lists the controllers and joysticks supported by the project. See [`src/controller_adapters/`](../src/controller_adapters/README.md) and [`src/joysticks/`](../src/joysticks/README.md) for the implementation.

Only Xbox 360, Wired Xbox One, and Keyboard are currently selectable via `control_via_gamepad.py --controller`; the other controllers below are run directly through their own adapter script (see their `__main__` blocks) rather than through that CLI's `auto`-detection.

## 🖥 System Support

The controllers and joysticks are supported on the following systems:

| Controller     | Windows | Linux | macOS | Link                                                                                                                                      | Image                                                           |
| -------------- | ------- | ----- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Xbox 360       | ✅       | ✅     | ✅     | [Amazon](https://www.amazon.de/-/en/gp/product/B07SDFLVKD/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)                                 | [Image](./images/xbox_pad.jpeg)                        |
| Wired Xbox One | ✅       | ✅     | ❌     | [Amazon](https://www.amazon.de/-/en/gp/product/B0977MTK65/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1)                                 | [Image](./images/xbox_one_turtle_beach_controller.jpg) |
| Logitech F710  | ✅       | ✅     | ❌     | [Logitech](https://www.logitechg.com/en-us/products/gamepads/f710-wireless-gamepad.940-000117.html)                                       | [Image](./images/Logitech.png)                         |
| GC102          | ✅       | ❌     | ❌     | [Amazon](https://www.amazon.com.au/Controller-Joystick-Gamepad-Dual-Vibration-Compatible/dp/B089RJK8KF)                                   | [Image](./images/gc102.jpg)                            |
| TectInter      | ✅       | ❌     | ❌     | [Ali Express](https://de.aliexpress.com/item/32824692489.html?spm=a2g0o.order_list.order_list_main.5.21ef5c5fW1dSEn&gatewayAdapt=glo2deu) | [Image](./images/tectinter_ps3.png)                    |

### 🗂 Legend:

- ✅: Supported
- ❌: Not Supported
- ❓: Unknown

