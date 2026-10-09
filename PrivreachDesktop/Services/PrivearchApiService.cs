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

    public void EnsureServerProcessRunning()
    {
        Task.Run(EnsureServerProcessRunningAsync);
    }

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
                if (File.Exists(Path.Combine(dir.FullName, "requirements.txt")) && Directory.Exists(Path.Combine(dir.FullName, "privearch")))
                {
                    repoRoot = dir.FullName;
                    break;
                }
                dir = dir.Parent;
            }

            if (repoRoot != null)
            {
                var pythonExe = Path.Combine(repoRoot, @"venv\Scripts\python.exe");
                var serverScript = Path.Combine(repoRoot, @"privearch\desktop_server.py");

                if (File.Exists(pythonExe) && File.Exists(serverScript))
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
                    Process.Start(psi);
                    await Task.Delay(2000).ConfigureAwait(false);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Failed to auto-launch server: {ex.Message}");
        }
    }
}
