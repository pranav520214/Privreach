using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.UI;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Windows.Graphics;
using PrivreachDesktop.ViewModels;

namespace PrivreachDesktop;

public sealed partial class MainWindow : Window
{
    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    private readonly List<string> _availableCommands = new()
    {
        "Ingest Scientific PDF Textbook...",
        "Clear Knowledge Vault & Reset Cache",
        "Check for Updates & System Patches",
        "Switch Model: Qwen 2.5 Coder 3B",
        "Switch Model: MedGemma 4B (Clinical)",
        "Start Local Ollama AI Engine",
        "Refresh System Status & VRAM",
        "Toggle Zero-Trust Airgap Policy"
    };

    public MainWindow()
    {
        App.LogStartup("MainWindow: constructor started");
        InitializeComponent();
        App.LogStartup("MainWindow: InitializeComponent completed");

        try
        {
            ExtendsContentIntoTitleBar = true;
            SetTitleBar(AppTitleBar);
            App.LogStartup("MainWindow: SetTitleBar completed");
        }
        catch (Exception ex)
        {
            App.LogStartup($"MainWindow: TitleBar exception: {ex.Message}");
        }

        try
        {
            var iconPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Assets", "AppIcon.ico");
            if (System.IO.File.Exists(iconPath))
            {
                AppWindow.SetIcon(iconPath);
                App.LogStartup("MainWindow: AppWindow.SetIcon completed");
            }
        }
        catch (Exception ex)
        {
            App.LogStartup($"MainWindow: SetIcon exception: {ex.Message}");
        }

        try
        {
            // Window Sizing according to Fluent Design Multi-Pane rubric
            var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(this);
            var dpi = GetDpiForWindow(hwnd);
            if (dpi == 0) dpi = 96;
            var scale = Math.Max(1.0, dpi / 96.0);

            // Target: 1480 x 920 DIP
            int widthPx = Math.Max(1200, (int)(1480 * scale));
            int heightPx = Math.Max(800, (int)(920 * scale));
            AppWindow.Resize(new SizeInt32(widthPx, heightPx));
            AppWindow.Show(true);
            SetForegroundWindow(hwnd);
            App.LogStartup($"MainWindow: AppWindow.Resize completed ({widthPx}x{heightPx}, hwnd=0x{hwnd:X})");
        }
        catch (Exception ex)
        {
            App.LogStartup($"MainWindow: Window resize exception: {ex.Message}");
        }

        // Navigate RootFrame to MainPage
        App.LogStartup("MainWindow: Navigating RootFrame to MainPage...");
        RootFrame.Navigate(typeof(MainPage));
        App.LogStartup("MainWindow: RootFrame.Navigate completed");
    }

    private async void OpenCommandPalette_Invoked(KeyboardAccelerator sender, KeyboardAcceleratorInvokedEventArgs args)
    {
        args.Handled = true;
        CommandPaletteDialog.XamlRoot = Content.XamlRoot;
        await CommandPaletteDialog.ShowAsync();
    }

    private void CommandSuggestBox_TextChanged(AutoSuggestBox sender, AutoSuggestBoxTextChangedEventArgs args)
    {
        if (args.Reason == AutoSuggestionBoxTextChangeReason.UserInput)
        {
            var query = sender.Text.ToLowerInvariant();
            sender.ItemsSource = _availableCommands
                .Where(c => c.ToLowerInvariant().Contains(query))
                .ToList();
        }
    }

    private void CommandSuggestBox_SuggestionChosen(AutoSuggestBox sender, AutoSuggestBoxSuggestionChosenEventArgs args)
    {
        if (args.SelectedItem is string chosen)
        {
            ExecuteCommand(chosen);
            CommandPaletteDialog.Hide();
        }
    }

    private void CommandListView_ItemClick(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is ListViewItem item && item.Tag is string tag)
        {
            ExecuteCommand(tag);
            CommandPaletteDialog.Hide();
        }
    }

    private void CommandPalette_ExecuteClick(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        var text = CommandSuggestBox.Text;
        if (!string.IsNullOrWhiteSpace(text))
        {
            ExecuteCommand(text);
        }
    }

    private async void ExecuteCommand(string cmd)
    {
        var mainPage = RootFrame.Content as MainPage;
        var vm = mainPage?.ViewModel;
        if (vm == null) return;

        if (cmd.Contains("clear") || cmd.Contains("Clear"))
        {
            await vm.ClearVaultAsync();
        }
        else if (cmd.Contains("update") || cmd.Contains("Update"))
        {
            await vm.CheckForUpdatesAsync();
        }
        else if (cmd.Contains("qwen2.5-coder:3b") || cmd.Contains("Qwen"))
        {
            await vm.SwitchModelAsync("qwen2.5-coder:3b");
        }
        else if (cmd.Contains("medgemma:4b") || cmd.Contains("MedGemma"))
        {
            await vm.SwitchModelAsync("medgemma:4b");
        }
        else if (cmd.Contains("start_ollama") || cmd.Contains("Ollama"))
        {
            await vm.StartOllamaAsync();
        }
        else if (cmd.Contains("refresh") || cmd.Contains("Status"))
        {
            await vm.RefreshStatusAsync();
        }
        else if (cmd.Contains("ingest") || cmd.Contains("Ingest"))
        {
            // Trigger sample ingestion or status refresh
            await vm.RefreshDocumentsAsync();
        }
    }
}
