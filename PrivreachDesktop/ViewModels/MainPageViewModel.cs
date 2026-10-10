using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.UI.Dispatching;
using PrivreachDesktop.Models;
using PrivreachDesktop.Services;

namespace PrivreachDesktop.ViewModels;

public partial class MainPageViewModel : ObservableObject
{
    private readonly PrivearchApiService _api = PrivearchApiService.Instance;
    private DispatcherQueue? _dispatcherQueue;

    [ObservableProperty]
    private string _queryText = "";

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string _statusMessage = "Ready";

    [ObservableProperty]
    private SystemStatusDto? _systemStatus;

    [ObservableProperty]
    private string _engineStatusText = "Connecting...";

    [ObservableProperty]
    private string _memoryStatusText = "RAM: -- MB";

    [ObservableProperty]
    private string _vaultStatusText = "Vault: 0 Chunks";

    [ObservableProperty]
    private QueryResultDto? _currentResult;

    [ObservableProperty]
    private QueryAnalysisDto? _queryAnalysis;

    [ObservableProperty]
    private CalculationAuditDto? _calculationAudit;

    [ObservableProperty]
    private bool _hasResults;

    [ObservableProperty]
    private bool _hasCalculation;

    [ObservableProperty]
    private string _visualEvidenceMarkdown = "";

    [ObservableProperty]
    private bool _hasVisualEvidence;

    [ObservableProperty]
    private bool _deepThinkingEnabled = true;

    [ObservableProperty]
    private string _reasoningTrace = "";

    [ObservableProperty]
    private bool _hasReasoningTrace;

    [ObservableProperty]
    private string _thinkingDurationText = "";

    [ObservableProperty]
    private string _deepThinkingMarkdown = "";

    [ObservableProperty]
    private string _graphMarkdown = "";

    [ObservableProperty]
    private bool _hasGraphData;

    [ObservableProperty]
    private string _graphStatsText = "0 Nodes • 0 Bridges";

    [ObservableProperty]
    private int _crossDocumentBridgesCount;

    [ObservableProperty]
    private double _groundingScore;

    [ObservableProperty]
    private string _groundingScoreText = "0% Grounded";

    [ObservableProperty]
    private ClaimDto? _selectedClaim;

    [ObservableProperty]
    private RetrievedChunkDto? _selectedChunk;

    [ObservableProperty]
    private string _activePdfUrl = "about:blank";

    [ObservableProperty]
    private string _activePdfDocName = "No Document Loaded";

    [ObservableProperty]
    private int _activePdfPage = 1;

    [ObservableProperty]
    private string _selectedSynthesisModel = "qwen2.5-coder:3b";

    [ObservableProperty]
    private string _selectedNavSection = "Research";

    [ObservableProperty]
    private string _selectedResearchDomain = "Aerospace";

    [ObservableProperty]
    private bool _isResearchExpanded = true;

    [ObservableProperty]
    private string _activeCenterTab = "3D Model";

    [ObservableProperty]
    private string _matrixResolution = "100×100";

    [ObservableProperty]
    private string _matrixFps = "60 fps";

    [ObservableProperty]
    private string _matrixViewMode = "Grid View";

    [ObservableProperty]
    private string _matrixProgressText = "Computational Matrix Loaded • 94%";

    [ObservableProperty]
    private double _matrixProgressPct = 94.0;

    // Scientific & Aerodynamic Metrics
    [ObservableProperty]
    private string _machNumber = "0.78";

    [ObservableProperty]
    private string _reynoldsNumber = "6.5 × 10⁶";

    [ObservableProperty]
    private string _boundaryLayer = "0.012 m";

    [ObservableProperty]
    private string _vorticity = "42.8 s⁻¹";

    [ObservableProperty]
    private string _liftToDragRatio = "18.42 L/D";

    [ObservableProperty]
    private string _dragCoefficient = "0.0245 Cd";

    [ObservableProperty]
    private string _liftCoefficient = "0.452 Cl";

    [ObservableProperty]
    private string _stallAngle = "14.2° AoA";

    [ObservableProperty]
    private string _activeProjectTitle = "Aerodynamic Analysis of Wing Design";

    [ObservableProperty]
    private string _governingEquation = "C_L = 2L / (ρ v² S) • C_D = C_{D0} + C_L² / (π e AR) • Subsonic Cruise Mach 0.78";

    // Hardware resource monitor meters
    [ObservableProperty]
    private double _cpuUsagePct = 0.0;

    [ObservableProperty]
    private string _cpuUsageDisplay = "0%";

    [ObservableProperty]
    private double _gpuUsagePct = 0.0;

    [ObservableProperty]
    private string _gpuUsageDisplay = "0%";

    [ObservableProperty]
    private string _ramUsageDisplay = "0.0 / 32 GB";

    [ObservableProperty]
    private string _vramUsageDisplay = "0.0 / 16 GB";

    [ObservableProperty]
    private double _ramUsagePct = 0.0;

    [ObservableProperty]
    private double _vramUsagePct = 0.0;

    // Real Model Status & Runtime indicators
    [ObservableProperty]
    private string _modelDisplayName = "Gemma 3 1B IT";

    [ObservableProperty]
    private string _modelStatusBadgeText = "Connecting...";

    [ObservableProperty]
    private string _modelEngineSubtitle = "Native GGUF / Ollama Engine";

    [ObservableProperty]
    private bool _isModelOnline = false;

    // Chat Conversation & Real Synthesis Text
    [ObservableProperty]
    private string _chatSynthesisText = "Privreach OS ready. Ingest a scientific textbook (PDF) or ask any computational question to begin.";

    [ObservableProperty]
    private string _primaryCitationText = "";

    // Processing wave progression (0 to 6)
    [ObservableProperty]
    private int _processingWaveStage = 6;

    [ObservableProperty]
    private string _activeProcessingStageName = "complete";

    [ObservableProperty]
    private string _chatQueryText = "Privreach Zero-Trust Scientific Workstation initialized. Ready for research inquiry.";

    public ObservableCollection<string> AttachedFiles { get; } = new();

    public ObservableCollection<ClaimDto> Claims { get; } = new();
    public ObservableCollection<RetrievedChunkDto> RetrievedChunks { get; } = new();
    public ObservableCollection<ReasoningStepDto> ReasoningSteps { get; } = new();
    public ObservableCollection<CrossDocBridgeDto> CrossDocBridges { get; } = new();
    public ObservableCollection<DocumentDto> Documents { get; } = new();
    public ObservableCollection<string> AvailableModels { get; } = new();

    public MainPageViewModel()
    {
        _dispatcherQueue = DispatcherQueue.GetForCurrentThread();
        if (_dispatcherQueue != null)
        {
            _dispatcherQueue.TryEnqueue(async () => await InitializeAsync());
        }
        else
        {
            Task.Run(async () => await InitializeAsync());
        }
    }

    public async Task InitializeAsync()
    {
        await _api.EnsureServerProcessRunningAsync();
        await RefreshStatusAsync();
        await RefreshDocumentsAsync();
        await RefreshModelsAsync();
    }

    [RelayCommand]
    public async Task RefreshStatusAsync()
    {
        var status = await _api.GetStatusAsync();
        if (status != null)
        {
            SystemStatus = status;
            EngineStatusText = status.EngineRunning ? $"Engine Online • Port {status.OllamaPort}" : "Engine Offline";
            MemoryStatusText = $"RAM: {status.RamUsageMb:F0} MB | VRAM: {status.VramUsageMb:F0} MB";
            VaultStatusText = $"Vault: {status.TotalChunks} Chunks ({status.IndexedDocuments} Docs)";
            if (!string.IsNullOrEmpty(status.SynthesisModel))
            {
                SelectedSynthesisModel = status.SynthesisModel;
            }

            // Real Hardware Telemetry
            CpuUsagePct = Math.Clamp(status.CpuPercent, 0.0, 100.0);
            CpuUsageDisplay = $"{status.CpuPercent:F0}%";

            double ramGb = status.RamUsageMb / 1024.0;
            RamUsageDisplay = $"{ramGb:F1} / 32 GB";
            RamUsagePct = Math.Clamp((status.RamUsageMb / 32768.0) * 100.0, 2.0, 100.0);

            double vramGb = status.VramUsageMb / 1024.0;
            VramUsageDisplay = status.VramUsageMb > 0 ? $"{vramGb:F1} / 16 GB" : "0.0 / 16 GB";
            VramUsagePct = status.VramUsageMb > 0 ? Math.Clamp((status.VramUsageMb / 16384.0) * 100.0, 2.0, 100.0) : 0.0;
            GpuUsagePct = status.VramUsageMb > 0 ? Math.Clamp((status.VramUsageMb / 16384.0) * 100.0, 10.0, 100.0) : 0.0;
            GpuUsageDisplay = status.VramUsageMb > 0 ? $"{GpuUsagePct:F0}%" : "0%";

            // Real Model Runtime Status
            if (status.GemmaEmbedded)
            {
                ModelDisplayName = "Gemma 3 1B IT";
                ModelStatusBadgeText = "Online";
                ModelEngineSubtitle = "Native In-Process GGUF Engine";
                IsModelOnline = true;
            }
            else if (status.EngineRunning)
            {
                ModelDisplayName = !string.IsNullOrEmpty(status.SynthesisModel) ? status.SynthesisModel : "Local LLM";
                ModelStatusBadgeText = "Online";
                ModelEngineSubtitle = $"Ollama Host (Port {status.OllamaPort})";
                IsModelOnline = true;
            }
            else
            {
                ModelDisplayName = "Model Runtime Offline";
                ModelStatusBadgeText = "Unavailable";
                ModelEngineSubtitle = "Launch Ollama or check models/ directory";
                IsModelOnline = false;
            }
        }
        else
        {
            EngineStatusText = "Server Offline (Attempting Reconnect)";
            MemoryStatusText = "RAM: --";
            VaultStatusText = "Vault: Offline";
            ModelDisplayName = "Engine Offline";
            ModelStatusBadgeText = "Disconnected";
            ModelEngineSubtitle = "Backend engine starting...";
            IsModelOnline = false;
            CpuUsageDisplay = "0%";
            GpuUsageDisplay = "0%";
            RamUsageDisplay = "0.0 / 32 GB";
            VramUsageDisplay = "0.0 / 16 GB";
        }
    }

    [RelayCommand]
    public async Task RefreshDocumentsAsync()
    {
        var docRes = await _api.GetDocumentsAsync();
        if (docRes != null)
        {
            Documents.Clear();
            AttachedFiles.Clear();
            foreach (var doc in docRes.Documents)
            {
                Documents.Add(doc);
                AttachedFiles.Add(doc.DocName);
            }
            if (Documents.Count > 0 && ActivePdfDocName == "No Document Loaded")
            {
                var first = Documents[0];
                ActivePdfDocName = first.DocName;
                ActivePdfUrl = _api.GetPdfStreamUrl(first.Path, 1);
            }
        }
    }

    [RelayCommand]
    public async Task RefreshModelsAsync()
    {
        var mRes = await _api.GetModelsAsync();
        if (mRes != null)
        {
            AvailableModels.Clear();
            foreach (var m in mRes.Models)
            {
                AvailableModels.Add(m);
            }
        }
    }

    [RelayCommand]
    public void SetNavSection(string section)
    {
        SelectedNavSection = section;
    }

    [RelayCommand]
    public void SetDomain(string domain)
    {
        SelectedResearchDomain = domain;
        switch (domain)
        {
            case "Aerospace":
                ActiveProjectTitle = "Aerodynamic Analysis of Wing Design";
                GoverningEquation = "C_L = 2L / (ρ v² S) • C_D = C_{D0} + C_L² / (π e AR) • Subsonic Cruise Mach 0.78";
                LiftToDragRatio = "18.42 L/D";
                DragCoefficient = "0.0245 Cd";
                LiftCoefficient = "0.452 Cl";
                StallAngle = "14.2° AoA";
                MachNumber = "0.78";
                ReynoldsNumber = "6.5 × 10⁶";
                BoundaryLayer = "0.012 m";
                Vorticity = "42.8 s⁻¹";
                ChatQueryText = "Analyze the aerodynamic efficiency of the new NACA 64-416 airfoil design under subsonic cruise conditions...";
                break;
            case "Physics":
                ActiveProjectTitle = "Thermodynamic State Equation & Ideal Gas Expansion";
                GoverningEquation = "P = n R T / V • ΔU = Q - W • Adiabatic Index γ = 1.4";
                LiftToDragRatio = "P = 116.4 kPa";
                DragCoefficient = "V = 0.05 m³";
                LiftCoefficient = "n = 2.0 mol";
                StallAngle = "T = 350.0 K";
                MachNumber = "1.00 M";
                ReynoldsNumber = "2.1 × 10⁵";
                BoundaryLayer = "0.005 m";
                Vorticity = "0.0 s⁻¹";
                ChatQueryText = "Calculate the pressure of 2 moles of ideal gas occupying 0.05 m³ at 350 Kelvin using P = nRT / V.";
                break;
            case "Biology":
                ActiveProjectTitle = "Pharmacokinetics & Receptor Binding Kinetics of Tacrolimus";
                GoverningEquation = "CL = V_d × k_el • AUC = Dose / CL • Bioavailability F = 0.25";
                LiftToDragRatio = "Kd = 0.4 nM";
                DragCoefficient = "CL = 0.06 L/h/kg";
                LiftCoefficient = "t1/2 = 12.0 h";
                StallAngle = "Vd = 1.0 L/kg";
                MachNumber = "0.00 M";
                ReynoldsNumber = "4.2 × 10³";
                BoundaryLayer = "0.001 m";
                Vorticity = "1.2 s⁻¹";
                ChatQueryText = "What is the clearance and bioavailability equation for tacrolimus in renal transplant recipients?";
                break;
            case "Chemistry":
                ActiveProjectTitle = "Gibbs Free Energy & Spontaneity of Chemical Equilibria";
                GoverningEquation = "ΔG = ΔH - T ΔS • K_eq = exp(-ΔG° / RT) • Le Chatelier Factor";
                LiftToDragRatio = "ΔG = -24.6 kJ/mol";
                DragCoefficient = "ΔH = -42.1 kJ/mol";
                LiftCoefficient = "ΔS = -58.7 J/mol·K";
                StallAngle = "K_eq = 2.1 × 10⁴";
                MachNumber = "0.00 M";
                ReynoldsNumber = "1.8 × 10⁴";
                BoundaryLayer = "0.002 m";
                Vorticity = "0.0 s⁻¹";
                ChatQueryText = "Derive Gibbs Free Energy ΔG = ΔH - TΔS and determine spontaneity criteria.";
                break;
            default:
                ActiveProjectTitle = $"{domain} Research & Computational Modeling";
                GoverningEquation = "f(x, t) = ∂²u/∂x² - (1/c²) ∂²u/∂t² = 0 • Convergent Mesh Formulation";
                break;
        }
    }

    [RelayCommand]
    public void SetCenterTab(string tab)
    {
        ActiveCenterTab = tab;
    }

    [RelayCommand]
    public void SetMatrixResolution(string res)
    {
        MatrixResolution = res;
    }

    [RelayCommand]
    public void SetMatrixViewMode(string mode)
    {
        MatrixViewMode = mode;
    }

    [RelayCommand]
    public async Task ExecuteQueryAsync()
    {
        if (string.IsNullOrWhiteSpace(QueryText))
            return;

        IsBusy = true;
        ProcessingWaveStage = 2; // analyzing & parsing
        ActiveProcessingStageName = "analyzing";
        ChatQueryText = QueryText;
        StatusMessage = "Analyzing query with 0.5B Router & Hybrid Retrieval...";

        try
        {
            ProcessingWaveStage = 3; // computing
            ActiveProcessingStageName = "computing";
            var res = await _api.QueryAsync(QueryText, deepThinking: DeepThinkingEnabled);
            ProcessingWaveStage = 5; // verifying
            ActiveProcessingStageName = "verifying";
            if (res != null)
            {
                ProcessingWaveStage = 6; // complete
                ActiveProcessingStageName = "generating";
                CurrentResult = res;
                QueryAnalysis = res.QueryAnalysis;
                CalculationAudit = res.CalculationAudit;
                HasResults = true;
                HasCalculation = res.CalculationAudit != null && !string.IsNullOrEmpty(res.CalculationAudit.EquationLatex);
                VisualEvidenceMarkdown = res.VisualEvidenceMarkdown ?? "";
                HasVisualEvidence = !string.IsNullOrWhiteSpace(res.VisualEvidenceMarkdown);

                ReasoningTrace = res.ReasoningTrace ?? "";
                HasReasoningTrace = !string.IsNullOrWhiteSpace(res.ReasoningTrace);
                DeepThinkingMarkdown = res.DeepThinkingMarkdown ?? "";
                ThinkingDurationText = res.ThinkingDurationS.HasValue ? $"{res.ThinkingDurationS.Value:F1}s" : "";

                ReasoningSteps.Clear();
                foreach (var s in res.ReasoningSteps)
                {
                    ReasoningSteps.Add(s);
                }

                // Update GraphRAG & Cross-Document Citation Network
                GraphMarkdown = res.GraphMarkdown ?? "";
                HasGraphData = !string.IsNullOrWhiteSpace(res.GraphMarkdown) || res.CrossDocBridges.Count > 0;
                CrossDocumentBridgesCount = res.CrossDocBridges.Count;
                if (res.GraphSubnetwork != null && res.GraphSubnetwork.TotalNodes > 0)
                {
                    GraphStatsText = $"{res.GraphSubnetwork.TotalNodes} Nodes • {res.GraphSubnetwork.TotalEdges} Edges • {res.CrossDocBridges.Count} Bridges";
                }
                else
                {
                    GraphStatsText = $"{res.CrossDocBridges.Count} Cross-Doc Bridges";
                }

                CrossDocBridges.Clear();
                foreach (var b in res.CrossDocBridges)
                {
                    CrossDocBridges.Add(b);
                }

                // Update Verification Claims
                Claims.Clear();
                if (res.Verification != null)
                {
                    GroundingScore = res.Verification.GroundingConfidencePct;
                    GroundingScoreText = $"{res.Verification.GroundingConfidencePct:F0}% Grounded";
                    foreach (var c in res.Verification.Claims)
                    {
                        Claims.Add(c);
                    }
                }

                // Update Retrieved Chunks
                RetrievedChunks.Clear();
                foreach (var chunk in res.RetrievedChunks)
                {
                    RetrievedChunks.Add(chunk);
                }

                // If claims exist, select first claim and jump PDF
                if (Claims.Count > 0)
                {
                    SelectClaim(Claims[0]);
                }
                else if (RetrievedChunks.Count > 0)
                {
                    SelectChunk(RetrievedChunks[0]);
                }

                ChatSynthesisText = res.SynthesisText;
                if (Claims.Count > 0)
                {
                    PrimaryCitationText = $"📄 [{Claims[0].ClaimId}] {Claims[0].SourceDoc} (p. {Claims[0].SourcePage ?? 1})";
                }
                else if (RetrievedChunks.Count > 0)
                {
                    PrimaryCitationText = $"📄 [1] {RetrievedChunks[0].DocName} (p. {RetrievedChunks[0].PageNum})";
                }
                else
                {
                    PrimaryCitationText = "✓ Local Synthesis Completed";
                }

                if (res.CalculationAudit != null && !string.IsNullOrEmpty(res.CalculationAudit.EquationLatex))
                {
                    var ca = res.CalculationAudit;
                    ActiveProjectTitle = $"Computation: {ca.TargetVariable} in {ca.EquationLatex}";
                    GoverningEquation = ca.EquationLatex;
                    LiftToDragRatio = $"{ca.TargetVariable} = {ca.DeterministicComputedValue:F4}";
                    DragCoefficient = $"Predicted: {ca.ModelPredictedValue:F4}";
                    LiftCoefficient = ca.IsVerified ? "Error: 0.0%" : $"Rel Err: {ca.RelativeErrorPct ?? 0.0:F2}%";
                    StallAngle = ca.VerificationStatus;
                }

                StatusMessage = $"Completed in {res.ExecutionStats.GetValueOrDefault("total_roundtrip_s", "0.0")}s";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"Inquiry Failed: {ex.Message}";
            ChatSynthesisText = $"⚠️ Inquiry error: {ex.Message}\n\nPlease check backend server status or model availability.";
            PrimaryCitationText = "Execution Failed";
        }
        finally
        {
            IsBusy = false;
            await RefreshStatusAsync();
        }
    }

    [RelayCommand]
    public void SetSamplePrompt(string prompt)
    {
        QueryText = prompt;
        _ = ExecuteQueryAsync();
    }

    [RelayCommand]
    public void SelectClaim(ClaimDto? claim)
    {
        if (claim == null) return;
        SelectedClaim = claim;

        if (!string.IsNullOrEmpty(claim.SourceDoc))
        {
            ActivePdfDocName = claim.SourceDoc;
            ActivePdfPage = claim.SourcePage ?? 1;

            var matchingDoc = Documents.FirstOrDefault(d => d.DocName == claim.SourceDoc);
            string path = matchingDoc != null ? matchingDoc.Path : claim.SourceDoc;
            ActivePdfUrl = _api.GetPdfStreamUrl(path, ActivePdfPage);
        }

        // Also highlight matching chunk in the list if available
        if (claim.SourcePage.HasValue)
        {
            var matchChunk = RetrievedChunks.FirstOrDefault(c => 
                c.DocName == claim.SourceDoc && c.PageNum == claim.SourcePage.Value);
            if (matchChunk != null)
            {
                SelectedChunk = matchChunk;
            }
        }
    }

    [RelayCommand]
    public void SelectChunk(RetrievedChunkDto? chunk)
    {
        if (chunk == null) return;
        SelectedChunk = chunk;
        ActivePdfDocName = chunk.DocName;
        ActivePdfPage = chunk.PageNum;

        var matchingDoc = Documents.FirstOrDefault(d => d.DocName == chunk.DocName);
        string path = matchingDoc != null ? matchingDoc.Path : chunk.DocName;
        ActivePdfUrl = _api.GetPdfStreamUrl(path, chunk.PageNum);
    }

    [RelayCommand]
    public async Task IngestFileAsync(string filePath)
    {
        if (string.IsNullOrWhiteSpace(filePath)) return;
        IsBusy = true;
        StatusMessage = $"Ingesting {System.IO.Path.GetFileName(filePath)}...";

        var res = await _api.IngestAsync(filePath);
        if (res != null && res.Status == "success")
        {
            StatusMessage = $"✓ Successfully ingested {res.DocName} ({res.Chunks} chunks)";
            await RefreshStatusAsync();
            await RefreshDocumentsAsync();
        }
        else
        {
            StatusMessage = $"Ingestion error: {res?.Error ?? "Unknown error"}";
        }
        IsBusy = false;
    }

    [RelayCommand]
    public async Task SwitchModelAsync(string model)
    {
        if (string.IsNullOrWhiteSpace(model)) return;
        IsBusy = true;
        StatusMessage = $"Switching synthesis engine to {model}...";

        bool ok = await _api.SwitchModelAsync("synthesis", model);
        if (ok)
        {
            SelectedSynthesisModel = model;
            StatusMessage = $"Active synthesis model switched to {model}";
        }
        else
        {
            StatusMessage = $"Failed to switch model to {model}";
        }
        IsBusy = false;
        await RefreshStatusAsync();
    }

    [RelayCommand]
    public async Task StartOllamaAsync()
    {
        IsBusy = true;
        StatusMessage = "Starting local Ollama AI Engine...";
        bool ok = await _api.StartEngineAsync();
        StatusMessage = ok ? "Local Ollama engine signal sent." : "Failed to trigger Ollama engine start.";
        IsBusy = false;
        await RefreshStatusAsync();
    }

    [RelayCommand]
    public async Task ClearVaultAsync()
    {
        IsBusy = true;
        StatusMessage = "Clearing knowledge vault and resetting index...";
        bool ok = await _api.ClearVaultAsync();
        if (ok)
        {
            Documents.Clear();
            RetrievedChunks.Clear();
            Claims.Clear();
            ActivePdfDocName = "No Document Loaded";
            ActivePdfUrl = "about:blank";
            StatusMessage = "Knowledge vault cleared. Ready for fresh documents.";
        }
        else
        {
            StatusMessage = "Failed to clear knowledge vault.";
        }
        IsBusy = false;
        await RefreshStatusAsync();
        await RefreshDocumentsAsync();
    }

    [ObservableProperty]
    private string _updaterNotificationText = "";

    [ObservableProperty]
    private bool _hasUpdaterNotification;

    [RelayCommand]
    public async Task CheckForUpdatesAsync()
    {
        StatusMessage = "Checking for system updates and patches...";
        var res = await _api.CheckForUpdatesAsync();
        if (res != null)
        {
            if (res.HasUpdate)
            {
                UpdaterNotificationText = $"Update v{res.LatestVersion} Available! {res.Changelog}";
                HasUpdaterNotification = true;
                StatusMessage = $"Update available: v{res.LatestVersion}";
            }
            else
            {
                UpdaterNotificationText = $"Privreach OS is up to date (v{res.CurrentVersion}).";
                HasUpdaterNotification = true;
                StatusMessage = $"System is up to date (v{res.CurrentVersion}).";
            }
        }
    }
}
