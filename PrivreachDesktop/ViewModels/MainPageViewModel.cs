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
            EngineStatusText = status.EngineRunning ? $"Ollama Online • Port {status.OllamaPort}" : "Ollama Offline";
            MemoryStatusText = $"RAM: {status.RamUsageMb:F0} MB | VRAM: {status.VramUsageMb:F0} MB";
            VaultStatusText = $"Vault: {status.TotalChunks} Chunks ({status.IndexedDocuments} Docs)";
            if (!string.IsNullOrEmpty(status.SynthesisModel))
            {
                SelectedSynthesisModel = status.SynthesisModel;
            }
        }
        else
        {
            EngineStatusText = "Server Offline (Attempting Reconnect)";
            MemoryStatusText = "RAM: --";
            VaultStatusText = "Vault: Offline";
        }
    }

    [RelayCommand]
    public async Task RefreshDocumentsAsync()
    {
        var docRes = await _api.GetDocumentsAsync();
        if (docRes != null)
        {
            Documents.Clear();
            foreach (var doc in docRes.Documents)
            {
                Documents.Add(doc);
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
    public async Task ExecuteQueryAsync()
    {
        if (string.IsNullOrWhiteSpace(QueryText))
            return;

        IsBusy = true;
        StatusMessage = "Analyzing query with 0.5B Router & Hybrid Retreival...";

        try
        {
            var res = await _api.QueryAsync(QueryText, deepThinking: DeepThinkingEnabled);
            if (res != null)
            {
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

                StatusMessage = $"Completed in {res.ExecutionStats.GetValueOrDefault("total_roundtrip_s", "0.0")}s";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"Inquiry Failed: {ex.Message}";
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
