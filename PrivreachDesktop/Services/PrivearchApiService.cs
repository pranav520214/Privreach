using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;
using PrivreachDesktop.Models;

namespace PrivreachDesktop.Services;

public class PrivearchApiService
{
    private static readonly Lazy<PrivearchApiService> _instance = new(() => new PrivearchApiService());
    public static PrivearchApiService Instance => _instance.Value;

    private readonly HttpClient _httpClient;
    private const string BaseUrl = "http://127.0.0.1:8765";

    public PrivearchApiService()
    {
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(240) // scientific synthesis can take time
        };
    }

    public async Task<SystemStatusDto?> GetStatusAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<SystemStatusDto>("/api/status").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<QueryResultDto?> QueryAsync(string query, bool deepThinking = true)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/query", new { query, deep_thinking = deepThinking }).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                var errorText = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                throw new Exception($"Query failed ({response.StatusCode}): {errorText}");
            }
            return await response.Content.ReadFromJsonAsync<QueryResultDto>().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[QueryAsync Error] {ex.Message}");
            throw;
        }
    }

    public async Task<IngestResultDto?> IngestAsync(string filePath)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/ingest", new { path = filePath }).ConfigureAwait(false);
            return await response.Content.ReadFromJsonAsync<IngestResultDto>().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"[IngestAsync Error] {ex.Message}");
            return new IngestResultDto { Status = "error", Error = ex.Message };
        }
    }

    public async Task<DocumentsResultDto?> GetDocumentsAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<DocumentsResultDto>("/api/documents").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<ModelsResultDto?> GetModelsAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<ModelsResultDto>("/api/models").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<GraphSubnetworkDto?> GetGraphAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<GraphSubnetworkDto>("/api/graph").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<bool> SwitchModelAsync(string role, string model)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/models/switch", new { role, model }).ConfigureAwait(false);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<bool> StartEngineAsync()
    {
        try
        {
            var response = await _httpClient.PostAsync("/api/engine/start", null).ConfigureAwait(false);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public string GetPdfStreamUrl(string filePath, int pageNum = 1)
    {
        return $"{BaseUrl}/api/pdf?path={Uri.EscapeDataString(filePath)}#page={pageNum}";
    }

    public async Task<SolveResultDto?> SolveEquationAsync(string equation, string targetVariable, object variables)
    {
        try
        {
            var res = await _httpClient.PostAsJsonAsync("/api/compute/solve", new
            {
                equation,
                target_variable = targetVariable,
                variables
            }).ConfigureAwait(false);

            return await res.Content.ReadFromJsonAsync<SolveResultDto>().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            return new SolveResultDto { Success = false, Error = ex.Message };
        }
    }

    public async Task<ArtifactsResultDto?> GetArtifactsAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<ArtifactsResultDto>("/api/artifacts").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<UpdaterStatusDto?> GetUpdaterStatusAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<UpdaterStatusDto>("/api/updater/status").ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<UpdateCheckResultDto?> CheckForUpdatesAsync()
    {
        try
        {
            var res = await _httpClient.PostAsync("/api/updater/check", null).ConfigureAwait(false);
            return await res.Content.ReadFromJsonAsync<UpdateCheckResultDto>().ConfigureAwait(false);
        }
        catch
        {
            return null;
        }
    }

    public async Task<PatchResultDto?> ApplyPatchAsync(string patchPath)
    {
        try
        {
            var res = await _httpClient.PostAsJsonAsync("/api/updater/apply", new { patch_path = patchPath }).ConfigureAwait(false);
            return await res.Content.ReadFromJsonAsync<PatchResultDto>().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            return new PatchResultDto { Success = false, Message = ex.Message, Error = ex.Message };
        }
    }

    public async Task<RollbackResultDto?> RollbackAsync(string? snapshotId = null)
    {
        try
        {
            var res = await _httpClient.PostAsJsonAsync("/api/updater/rollback", new { snapshot_id = snapshotId }).ConfigureAwait(false);
            return await res.Content.ReadFromJsonAsync<RollbackResultDto>().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            return new RollbackResultDto { Success = false, Message = ex.Message, Error = ex.Message };
        }
    }

    public async Task<bool> ClearVaultAsync()
    {
        try
        {
            var res = await _httpClient.PostAsync("/api/vault/clear", null).ConfigureAwait(false);
            return res.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public void EnsureServerProcessRunning()
    {
        Task.Run(EnsureServerProcessRunningAsync);
    }

    private static Process? _serverProcess;

    public async Task EnsureServerProcessRunningAsync()
    {
        try
        {
            var status = await GetStatusAsync().ConfigureAwait(false);
            if (status != null)
            {
                return; // Already running!
            }
        }
        catch { }

        // Attempt to launch desktop_server.py in background
        try
        {
            var appDir = AppDomain.CurrentDomain.BaseDirectory;
            var dir = new DirectoryInfo(appDir);
            string? repoRoot = null;
            while (dir != null)
            {
                if (Directory.Exists(Path.Combine(dir.FullName, "privreach")) ||
                    Directory.Exists(Path.Combine(dir.FullName, "privearch")) ||
                    File.Exists(Path.Combine(dir.FullName, "pyproject.toml")) ||
                    File.Exists(Path.Combine(dir.FullName, "requirements.txt")))
                {
                    repoRoot = dir.FullName;
                    break;
                }
                dir = dir.Parent;
            }

            // 1. Check if compiled standalone backend binary exists
            string[] engineExeCandidates =
            {
                Path.Combine(appDir, "privreach_engine", "privreach_engine.exe"),
                Path.Combine(appDir, "engine", "privreach_engine.exe"),
                Path.Combine(appDir, "privreach_engine.exe"),
                repoRoot != null ? Path.Combine(repoRoot, @"dist\privreach_engine\privreach_engine.exe") : "",
                repoRoot != null ? Path.Combine(repoRoot, "privreach_engine.exe") : ""
            };

            string? standaloneEngine = engineExeCandidates.FirstOrDefault(p => !string.IsNullOrEmpty(p) && File.Exists(p));
            App.LogStartup($"EnsureServerProcessRunningAsync: standaloneEngine candidate = '{standaloneEngine}'");

            if (standaloneEngine != null)
            {
                App.LogStartup($"EnsureServerProcessRunningAsync: Starting process {standaloneEngine} on 127.0.0.1:8765");
                var psi = new ProcessStartInfo
                {
                    FileName = standaloneEngine,
                    Arguments = "127.0.0.1 8765",
                    WorkingDirectory = Path.GetDirectoryName(standaloneEngine)!,
                    CreateNoWindow = true,
                    UseShellExecute = false
                };
                _serverProcess = Process.Start(psi);
                App.LogStartup($"EnsureServerProcessRunningAsync: Process started with PID {_serverProcess?.Id}");
            }
            else if (repoRoot != null)
            {
                string[] pythonCandidates =
                {
                    Path.Combine(repoRoot, @"venv\Scripts\python.exe"),
                    Path.Combine(repoRoot, @".venv\Scripts\python.exe"),
                    "python.exe"
                };

                string? pythonExe = pythonCandidates.FirstOrDefault(File.Exists) ?? "python.exe";

                string[] scriptCandidates =
                {
                    Path.Combine(repoRoot, @"privreach\desktop_server.py"),
                    Path.Combine(repoRoot, @"privearch\desktop_server.py")
                };

                string? serverScript = scriptCandidates.FirstOrDefault(File.Exists);

                if (serverScript != null)
                {
                    var psi = new ProcessStartInfo
                    {
                        FileName = pythonExe,
                        Arguments = $"\"{serverScript}\" 127.0.0.1 8765",
                        WorkingDirectory = repoRoot,
                        CreateNoWindow = true,
                        UseShellExecute = false
                    };
                    psi.EnvironmentVariables["PYTHONPATH"] = repoRoot;
                    _serverProcess = Process.Start(psi);
                }
            }

            // Poll until server is ready (up to 15 seconds)
            for (int i = 0; i < 30; i++)
            {
                await Task.Delay(500).ConfigureAwait(false);
                var testStatus = await GetStatusAsync().ConfigureAwait(false);
                if (testStatus != null)
                {
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            App.LogStartup($"Failed to auto-launch server: {ex.Message}\n{ex.StackTrace}");
            Debug.WriteLine($"Failed to auto-launch server: {ex.Message}");
        }
    }
}
