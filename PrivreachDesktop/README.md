# Privreach Desktop — Native WinUI 3 Research Workstation

**Privreach Desktop** is the native Windows client for Privreach OS, built with **.NET 8** and the **Windows App SDK (WinUI 3)**.

---

## 🌟 Architecture & Features

- **Fluent Design System**: Minimalist light skeuomorphic aesthetic with soft borders, gentle ambient depth, and pale blue accents.
- **Three-Panel Research Layout**:
  - **Left Navigation**: Collapsible section selector (Home, Research, Projects, Knowledge, Settings) and quick domain switcher (Aerospace, Physics, Biology, Chemistry).
  - **Center Canvas**: Interactive 100×100 computational dot matrix fluid simulation, 3D model visualizer, and derivation audits.
  - **Right Inquiry & Verification Panel**: Synchronized adversarial research console, claim verification pills, and live chat synthesis.
- **Direct PDF Evidence Viewer**: Integrated Microsoft Edge **WebView2** supporting instantaneous page jumps (`/api/pdf?path=...#page=X`) when citation pills or verification claims are selected.
- **Live System Resource Telemetry**: Continuous dynamic monitoring of CPU utilization, system RAM (0.6 / 32 GB), GPU/VRAM allocation, and local model runtime engine indicators.
- **STA-Safe Asynchronous Dispatching**: Uses `Microsoft.UI.Dispatching.DispatcherQueue` for thread-safe UI updates.
- **MVVM Clean Architecture**: Built with `CommunityToolkit.Mvvm` (`ObservableObject`, `[ObservableProperty]`, `[RelayCommand]`).

---

## 🛠️ Project Structure

```
PrivreachDesktop/
├── Assets/                # Official logos, splash screens, and app icons
├── Models/
│   └── PrivearchModels.cs # Strongly typed Data Transfer Objects (DTOs) for backend APIs
├── Services/
│   └── PrivearchApiService.cs # Asynchronous HTTP client & automatic server daemon orchestration
├── ViewModels/
│   └── MainPageViewModel.cs  # Master ViewModel managing state, telemetry, and inquiries
├── App.xaml / App.xaml.cs    # Application entry point, global styles & brushes
├── MainWindow.xaml / .cs     # Main native window with custom TitleBar & window sizing
├── MainPage.xaml / .cs       # Master three-panel research workstation UI
└── PrivreachDesktop.csproj   # .NET 8 WinUI 3 project definition
```

---

## 🏗️ Building and Running

### Prerequisites
- Windows 10 (version 1809 or higher) or Windows 11
- [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- Visual Studio 2022 with *.NET Desktop Development* or `dotnet` CLI with Windows App Runtime

### Command-Line Build
To build the project for `win-x64`:
```powershell
dotnet build PrivreachDesktop\PrivreachDesktop.csproj -c Debug -r win-x64 -p:Platform=x64
```

### Launch
```powershell
# Using the Windows App CLI (recommended for unpackaged WinUI 3 apps)
winapp run PrivreachDesktop\PrivreachDesktop.csproj --detach

# Or launch via the root launcher script
.\run_desktop.ps1
```
