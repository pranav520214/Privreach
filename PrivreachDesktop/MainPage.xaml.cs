using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Imaging;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Storage.Pickers;
using Windows.ApplicationModel.DataTransfer;
using PrivreachDesktop.Models;
using PrivreachDesktop.ViewModels;

namespace PrivreachDesktop;

public sealed partial class MainPage : Page
{
    public MainPageViewModel ViewModel { get; }

    public MainPage()
    {
        App.LogStartup("MainPage: constructor started");
        InitializeComponent();
        App.LogStartup("MainPage: InitializeComponent completed");
        ViewModel = new MainPageViewModel();
        App.LogStartup("MainPage: ViewModel instantiated");
        DataContext = ViewModel;

        Loaded += MainPage_Loaded;
        ViewModel.PropertyChanged += ViewModel_PropertyChanged;
        App.LogStartup("MainPage: constructor finished");
    }

    public void SetDomain(string domain)
    {
        ViewModel.SetDomain(domain);
    }

    private void ViewModel_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(ViewModel.ActivePdfUrl))
        {
            NavigatePdf(ViewModel.ActivePdfUrl);
        }
        else if (e.PropertyName == nameof(ViewModel.MatrixResolution) || e.PropertyName == nameof(ViewModel.MatrixViewMode))
        {
            RenderMatrixFrame();
        }
    }

    private async void MainPage_Loaded(object sender, RoutedEventArgs e)
    {
        App.LogStartup("MainPage: Loaded event fired");
        InitializeMatrixRenderer();
        try
        {
            await PdfWebView.EnsureCoreWebView2Async();
            App.LogStartup("MainPage: EnsureCoreWebView2Async finished");

            if (PdfWebView.CoreWebView2 != null)
            {
                PdfWebView.CoreWebView2.Settings.IsStatusBarEnabled = false;
                PdfWebView.CoreWebView2.Settings.AreDevToolsEnabled = false;
                App.LogStartup("MainPage: CoreWebView2 settings configured");
            }

            if (!string.IsNullOrEmpty(ViewModel.ActivePdfUrl) && ViewModel.ActivePdfUrl != "about:blank")
            {
                NavigatePdf(ViewModel.ActivePdfUrl);
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"WebView2 initialization: {ex.Message}");
        }
    }

    // 100x100 Computational Matrix Live Renderer
    private Microsoft.UI.Xaml.Media.Imaging.WriteableBitmap? _matrixBitmap;
    private DispatcherTimer? _matrixTimer;
    private double _matrixPhase = 0;
    private const int MatrixPixelSize = 420;

    private void InitializeMatrixRenderer()
    {
        try
        {
            _matrixBitmap = new Microsoft.UI.Xaml.Media.Imaging.WriteableBitmap(MatrixPixelSize, MatrixPixelSize);
            if (MatrixCanvasImage != null)
            {
                MatrixCanvasImage.Source = _matrixBitmap;
            }

            _matrixTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(33) };
            _matrixTimer.Tick += (s, ev) =>
            {
                _matrixPhase += 0.08;
                RenderMatrixFrame();
            };
            _matrixTimer.Start();
            RenderMatrixFrame();
        }
        catch (Exception ex)
        {
            App.LogStartup($"InitializeMatrixRenderer exception: {ex.Message}");
        }
    }

    private void RenderMatrixFrame()
    {
        if (_matrixBitmap == null) return;

        try
        {
            int gridSize = ViewModel.MatrixResolution switch
            {
                "25×25" => 25,
                "50×50" => 50,
                _ => 100
            };

            string viewMode = ViewModel.MatrixViewMode;
            byte[] pixels = new byte[MatrixPixelSize * MatrixPixelSize * 4];

            // Background: pure clean white #FFFFFF
            for (int i = 0; i < pixels.Length; i += 4)
            {
                pixels[i] = 255;
                pixels[i + 1] = 255;
                pixels[i + 2] = 255;
                pixels[i + 3] = 255;
            }

            double step = (double)MatrixPixelSize / (gridSize + 1);
            int dotRadius = gridSize == 100 ? 1 : (gridSize == 50 ? 2 : 3);

            for (int gy = 0; gy < gridSize; gy++)
            {
                double y = (gy + 1) * step;
                for (int gx = 0; gx < gridSize; gx++)
                {
                    double x = (gx + 1) * step;
                    double normX = (double)gx / gridSize;
                    double dx = normX - 0.45;
                    double dy = ((double)gy / gridSize) - 0.5;
                    double dist = Math.Sqrt(dx * dx * 2.0 + dy * dy * 6.0);

                    double wave = Math.Sin(normX * 14.0 - _matrixPhase + Math.Exp(-dist * 4.0) * 2.0);

                    byte r, g, b;
                    if (viewMode == "Heatmap")
                    {
                        double val = Math.Clamp(0.5 + 0.5 * wave * Math.Exp(-dist * 2.0), 0.0, 1.0);
                        if (val < 0.5)
                        {
                            r = (byte)(37 + (16 - 37) * (val * 2));
                            g = (byte)(99 + (185 - 99) * (val * 2));
                            b = (byte)(235 + (129 - 235) * (val * 2));
                        }
                        else
                        {
                            r = (byte)(16 + (245 - 16) * ((val - 0.5) * 2));
                            g = (byte)(185 + (158 - 185) * ((val - 0.5) * 2));
                            b = (byte)(129 + (11 - 129) * ((val - 0.5) * 2));
                        }
                    }
                    else if (viewMode == "Vector Flow")
                    {
                        double intensity = 0.3 + 0.7 * Math.Max(0, wave);
                        r = (byte)(30 + (1 - intensity) * 160);
                        g = (byte)(64 + (1 - intensity) * 140);
                        b = (byte)(175 + (1 - intensity) * 60);
                    }
                    else
                    {
                        // Grid View: crisp dark navy / slate dots
                        double intensity = 0.35 + 0.65 * (0.5 + 0.5 * Math.Sin(normX * 10.0 - _matrixPhase));
                        byte darkVal = (byte)(230 - intensity * 200);
                        r = darkVal;
                        g = (byte)(darkVal + 6);
                        b = (byte)(darkVal + 20);
                    }

                    int px = (int)x;
                    int py = (int)y;

                    for (int ddy = -dotRadius; ddy <= dotRadius; ddy++)
                    {
                        int curY = py + ddy;
                        if (curY < 0 || curY >= MatrixPixelSize) continue;
                        for (int ddx = -dotRadius; ddx <= dotRadius; ddx++)
                        {
                            int curX = px + ddx;
                            if (curX < 0 || curX >= MatrixPixelSize) continue;

                            int idx = (curY * MatrixPixelSize + curX) * 4;
                            pixels[idx] = b;
                            pixels[idx + 1] = g;
                            pixels[idx + 2] = r;
                            pixels[idx + 3] = 255;
                        }
                    }
                }
            }

            using (var stream = _matrixBitmap.PixelBuffer.AsStream())
            {
                stream.Write(pixels, 0, pixels.Length);
            }
            _matrixBitmap.Invalidate();
        }
        catch { }
    }

    private void NavigatePdf(string url)
    {
        try
        {
            if (PdfWebView.CoreWebView2 != null && !string.IsNullOrEmpty(url) && Uri.TryCreate(url, UriKind.Absolute, out var uri))
            {
                PdfWebView.Source = uri;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"PDF navigation failed: {ex.Message}");
        }
    }

    private void SampleChip_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string prompt)
        {
            ViewModel.SetSamplePrompt(prompt);
        }
    }

    private void ClaimItem_Tapped(object sender, TappedRoutedEventArgs e)
    {
        if (sender is FrameworkElement elem && elem.DataContext is ClaimDto claim)
        {
            ViewModel.SelectClaim(claim);
        }
    }

    private void ClaimButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement elem && elem.DataContext is ClaimDto claim)
        {
            ViewModel.SelectClaim(claim);
        }
    }

    private void ChunkItem_Tapped(object sender, TappedRoutedEventArgs e)
    {
        if (sender is FrameworkElement elem && elem.DataContext is RetrievedChunkDto chunk)
        {
            ViewModel.SelectChunk(chunk);
        }
    }

    private async void IngestButton_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker();
        picker.ViewMode = PickerViewMode.List;
        picker.SuggestedStartLocation = PickerLocationId.DocumentsLibrary;
        picker.FileTypeFilter.Add(".pdf");
        picker.FileTypeFilter.Add(".mp4");
        picker.FileTypeFilter.Add(".mp3");
        picker.FileTypeFilter.Add(".wav");

        WinRT.Interop.InitializeWithWindow.Initialize(picker, App.WindowHandle);

        var file = await picker.PickSingleFileAsync();
        if (file != null)
        {
            await ViewModel.IngestFileAsync(file.Path);
        }
    }

    private async void ModelComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (sender is ComboBox cb && cb.SelectedItem is string newModel && newModel != ViewModel.SelectedSynthesisModel)
        {
            await ViewModel.SwitchModelAsync(newModel);
        }
    }

    private void RootGrid_DragOver(object sender, DragEventArgs e)
    {
        if (e.DataView.Contains(StandardDataFormats.StorageItems))
        {
            e.AcceptedOperation = DataPackageOperation.Copy;
            e.DragUIOverride.Caption = "Drop to Ingest into Knowledge Vault";
            e.DragUIOverride.IsCaptionVisible = true;
            e.DragUIOverride.IsGlyphVisible = true;
        }
    }

    private async void RootGrid_Drop(object sender, DragEventArgs e)
    {
        if (e.DataView.Contains(StandardDataFormats.StorageItems))
        {
            var items = await e.DataView.GetStorageItemsAsync();
            foreach (var item in items)
            {
                if (item is Windows.Storage.StorageFile file)
                {
                    var ext = Path.GetExtension(file.Path).ToLowerInvariant();
                    if (ext == ".pdf" || ext == ".mp4" || ext == ".mp3" || ext == ".wav")
                    {
                        await ViewModel.IngestFileAsync(file.Path);
                    }
                }
            }
        }
    }

    private void TabButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string tab)
        {
            ViewModel.SetCenterTab(tab);
        }
    }

    private void DomainButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string domain)
        {
            ViewModel.SetDomain(domain);
        }
    }

    private void NavIconButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string nav)
        {
            ViewModel.SetNavSection(nav);
        }
    }

    private void ResolutionButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string res)
        {
            ViewModel.SetMatrixResolution(res);
        }
    }

    private void ViewModeButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string mode)
        {
            ViewModel.SetMatrixViewMode(mode);
        }
    }

    private void ChatSend_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrWhiteSpace(ChatInputBox.Text))
        {
            ViewModel.QueryText = ChatInputBox.Text.Trim();
            ChatInputBox.Text = "";
            _ = ViewModel.ExecuteQueryAsync();
        }
    }

    private void ChatInputBox_KeyDown(object sender, KeyRoutedEventArgs e)
    {
        if (e.Key == Windows.System.VirtualKey.Enter && !Microsoft.UI.Input.InputKeyboardSource.GetKeyStateForCurrentThread(Windows.System.VirtualKey.Shift).HasFlag(Windows.UI.Core.CoreVirtualKeyStates.Down))
        {
            e.Handled = true;
            ChatSend_Click(sender, e);
        }
    }

    // Static helper brushes and converters for x:Bind
    private static readonly SolidColorBrush BluePillFill = new(Windows.UI.Color.FromArgb(255, 239, 246, 255));
    private static readonly SolidColorBrush BluePillStroke = new(Windows.UI.Color.FromArgb(255, 191, 219, 254));
    private static readonly SolidColorBrush BluePrimary = new(Windows.UI.Color.FromArgb(255, 37, 99, 235));
    private static readonly SolidColorBrush TextSlate = new(Windows.UI.Color.FromArgb(255, 100, 116, 139));
    private static readonly SolidColorBrush TextNavy = new(Windows.UI.Color.FromArgb(255, 15, 23, 42));
    private static readonly SolidColorBrush TransparentBrush = new(Microsoft.UI.Colors.Transparent);
    private static readonly SolidColorBrush GreenFill = new(Windows.UI.Color.FromArgb(255, 236, 253, 245));
    private static readonly SolidColorBrush GreenText = new(Windows.UI.Color.FromArgb(255, 16, 185, 129));
    private static readonly SolidColorBrush GreyFill = new(Windows.UI.Color.FromArgb(255, 241, 245, 249));
    private static readonly SolidColorBrush GreyText = new(Windows.UI.Color.FromArgb(255, 148, 163, 184));

    public static Brush TabToActiveBrush(string activeTab, string currentTab) =>
        activeTab == currentTab ? BluePillFill : TransparentBrush;

    public static Brush TabToBorderBrush(string activeTab, string currentTab) =>
        activeTab == currentTab ? BluePillStroke : TransparentBrush;

    public static Brush TabToForegroundBrush(string activeTab, string currentTab) =>
        activeTab == currentTab ? BluePrimary : TextSlate;

    public static Brush DomainToActiveBrush(string activeDomain, string currentDomain) =>
        activeDomain == currentDomain ? BluePillFill : TransparentBrush;

    public static Brush DomainToBorderBrush(string activeDomain, string currentDomain) =>
        activeDomain == currentDomain ? BluePillStroke : TransparentBrush;

    public static Brush DomainToForegroundBrush(string activeDomain, string currentDomain) =>
        activeDomain == currentDomain ? BluePrimary : TextNavy;

    public static Visibility TabToVisibility(string activeTab, string targetTab) =>
        activeTab == targetTab ? Visibility.Visible : Visibility.Collapsed;

    public static Visibility TabToInvertVisibility(string activeTab, string targetTab) =>
        activeTab != targetTab ? Visibility.Visible : Visibility.Collapsed;

    public static Brush StageToBadgeBrush(int currentStage, int targetStage) =>
        currentStage >= targetStage ? GreenFill : GreyFill;

    public static Brush StageToBadgeForeground(int currentStage, int targetStage) =>
        currentStage >= targetStage ? GreenText : GreyText;

    public static Visibility BoolToVisibility(bool v) => v ? Visibility.Visible : Visibility.Collapsed;
    public static Visibility InvertBoolToVisibility(bool v) => v ? Visibility.Collapsed : Visibility.Visible;
    public static Visibility IntToVisibility(int count) => count > 0 ? Visibility.Visible : Visibility.Collapsed;
    public static Visibility NotNullToVisibility(object? obj) => obj != null ? Visibility.Visible : Visibility.Collapsed;
    public static Visibility StringNotEmptyToVisibility(string? text) => !string.IsNullOrEmpty(text) ? Visibility.Visible : Visibility.Collapsed;
    public static bool Not(bool v) => !v;
    public static Brush StatusFillBrush(bool online) => online ? GreenFill : GreyFill;
    public static Brush StatusStrokeBrush(bool online) => online ? BluePillStroke : TransparentBrush;
    public static Brush StatusTextBrush(bool online) => online ? GreenText : TextSlate;
    public static string StatusBadgeText(bool online) => online ? "Verified" : "Ready";
    public static Microsoft.UI.Xaml.Media.Brush EngineRunningToBrush(bool running) => 
        running ? new Microsoft.UI.Xaml.Media.SolidColorBrush(Microsoft.UI.Colors.LimeGreen) 
                : new Microsoft.UI.Xaml.Media.SolidColorBrush(Microsoft.UI.Colors.OrangeRed);
}
