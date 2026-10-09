using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Data;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Navigation;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace PrivreachDesktop;

/// <summary>
/// Provides application-specific behavior to supplement the default Application class.
/// </summary>
public partial class App : Application
{
    /// <summary>
    /// The main application window. Use <c>App.Window</c> from any class that needs
    /// the window reference (for dialogs, pickers, interop, etc.).
    /// </summary>
    public static Window Window { get; private set; } = null!;

    /// <summary>
    /// The UI thread dispatcher. Use <c>App.DispatcherQueue</c> to marshal calls
    /// to the UI thread. Fully qualified to avoid CS0104 ambiguity with
    /// <see cref="Windows.System.DispatcherQueue"/>.
    /// </summary>
    public static Microsoft.UI.Dispatching.DispatcherQueue DispatcherQueue { get; private set; } = null!;

    /// <summary>
    /// The native window handle (HWND). Use for file pickers,
    /// <c>DataTransferManager</c>, and any WinRT interop that requires
    /// <c>InitializeWithWindow</c>.
    /// </summary>
    public static nint WindowHandle =>
        WinRT.Interop.WindowNative.GetWindowHandle(Window);

    public static void LogStartup(string msg)
    {
        try
        {
            var logPath = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Privreach", "startup.log");
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(logPath)!);
            System.IO.File.AppendAllText(logPath, $"[{DateTime.Now:HH:mm:ss.fff}] {msg}\r\n");
        }
        catch { }
    }

    /// <summary>
    /// Initializes the singleton application object.
    /// </summary>
    public App()
    {
        LogStartup("App constructor started");
        InitializeComponent();

        try
        {
            var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var webView2UserDataFolder = System.IO.Path.Combine(localAppData, "Privreach", "EBWebView");
            System.IO.Directory.CreateDirectory(webView2UserDataFolder);
            Environment.SetEnvironmentVariable("WEBVIEW2_USER_DATA_FOLDER", webView2UserDataFolder);
            LogStartup($"Configured WEBVIEW2_USER_DATA_FOLDER: {webView2UserDataFolder}");
        }
        catch (Exception ex)
        {
            LogStartup($"Failed to set WEBVIEW2_USER_DATA_FOLDER: {ex.Message}");
        }

        UnhandledException += (s, e) =>
        {
            LogStartup($"[FATAL UNHANDLED EXCEPTION] {e.Message} \n {e.Exception}");
            e.Handled = true;
        };
        LogStartup("App constructor finished");
    }

    /// <summary>
    /// Invoked when the application is launched.
    /// </summary>
    /// <param name="args">Details about the launch request and process.</param>
    protected override void OnLaunched(Microsoft.UI.Xaml.LaunchActivatedEventArgs args)
    {
        LogStartup("OnLaunched started");
        try
        {
            Window = new MainWindow();
            LogStartup("MainWindow instantiated");
            DispatcherQueue = Microsoft.UI.Dispatching.DispatcherQueue.GetForCurrentThread();
            LogStartup("DispatcherQueue retrieved, calling Window.Activate()");
            Window.Activate();
            LogStartup("Window.Activate() finished!");
        }
        catch (Exception ex)
        {
            LogStartup($"[CRITICAL OnLaunched Exception] {ex.Message}\n{ex.StackTrace}");
            throw;
        }
    }
}
