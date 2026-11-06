import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    self.contentViewController = flutterViewController

    // window_manager controls full-screen and resize lock on macOS.
    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
  }
}
