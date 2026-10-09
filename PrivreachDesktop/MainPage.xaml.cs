using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Windows.Storage.Pickers;
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

    private void ViewModel_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(ViewModel.ActivePdfUrl))
        {
            NavigatePdf(ViewModel.ActivePdfUrl);
        }
    }

    private async void MainPage_Loaded(object sender, RoutedEventArgs e)
    {
        App.LogStartup("MainPage: Loaded event fired");
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

    // Static helper converters for x:Bind
    public static Visibility BoolToVisibility(bool v) => v ? Visibility.Visible : Visibility.Collapsed;
    public static Visibility InvertBoolToVisibility(bool v) => v ? Visibility.Collapsed : Visibility.Visible;
    public static Visibility IntToVisibility(int count) => count > 0 ? Visibility.Visible : Visibility.Collapsed;
    public static Visibility NotNullToVisibility(object? obj) => obj != null ? Visibility.Visible : Visibility.Collapsed;
    public static bool Not(bool v) => !v;
    public static Microsoft.UI.Xaml.Media.Brush EngineRunningToBrush(bool running) => 
        running ? new Microsoft.UI.Xaml.Media.SolidColorBrush(Microsoft.UI.Colors.LimeGreen) 
                : new Microsoft.UI.Xaml.Media.SolidColorBrush(Microsoft.UI.Colors.OrangeRed);
}
