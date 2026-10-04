/**
 * Privearch Windows Native Launcher
 * Compiled into Privearch.exe
 */

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <shellapi.h>

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "shell32.lib")

#define DEFAULT_URL "http://127.0.0.1:7860"

static void set_console_utf8(void) {
    SetConsoleOutputCP(65001);
    SetConsoleCP(65001);
}

static int is_port_listening(int port) {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 0;

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        WSACleanup();
        return 0;
    }

    struct sockaddr_in client;
    client.sin_family = AF_INET;
    client.sin_addr.s_addr = inet_addr("127.0.0.1");
    client.sin_port = htons(port);

    int res = connect(sock, (struct sockaddr *)&client, sizeof(client));
    closesocket(sock);
    WSACleanup();
    return (res == 0);
}

static int find_python(char *out_path, size_t max_len) {
    if (GetEnvironmentVariableA("PRIVEARCH_PYTHON", out_path, (DWORD)max_len) > 0) {
        if (GetFileAttributesA(out_path) != INVALID_FILE_ATTRIBUTES) return 1;
    }

    if (SearchPathA(NULL, "python.exe", NULL, (DWORD)max_len, out_path, NULL) > 0) {
        return 1;
    }

    char local_app_data[MAX_PATH];
    if (GetEnvironmentVariableA("LOCALAPPDATA", local_app_data, MAX_PATH) > 0) {
        char candidate[MAX_PATH];
        snprintf(candidate, MAX_PATH, "%s\\Programs\\Python\\Python311\\python.exe", local_app_data);
        if (GetFileAttributesA(candidate) != INVALID_FILE_ATTRIBUTES) {
            strncpy(out_path, candidate, max_len);
            return 1;
        }
        snprintf(candidate, MAX_PATH, "%s\\Programs\\Python\\Python312\\python.exe", local_app_data);
        if (GetFileAttributesA(candidate) != INVALID_FILE_ATTRIBUTES) {
            strncpy(out_path, candidate, max_len);
            return 1;
        }
    }

    strncpy(out_path, "python.exe", max_len);
    return 1;
}

static void ensure_ollama_running(const char *python_path) {
    if (is_port_listening(11434)) {
        return;
    }

    char ollama_path[MAX_PATH];
    int found_ollama = (SearchPathA(NULL, "ollama.exe", NULL, MAX_PATH, ollama_path, NULL) != 0);
    if (!found_ollama) {
        char user_profile[MAX_PATH];
        if (GetEnvironmentVariableA("LOCALAPPDATA", user_profile, MAX_PATH) > 0) {
            snprintf(ollama_path, MAX_PATH, "%s\\Programs\\Ollama\\ollama.exe", user_profile);
            if (GetFileAttributesA(ollama_path) != INVALID_FILE_ATTRIBUTES) {
                found_ollama = 1;
            }
        }
    }

    if (!found_ollama) {
        printf("\n========================================================\n");
        printf("  ⚡ LOCAL AI ENGINE NOT DETECTED\n");
        printf("  Privearch will now automatically download and\n");
        printf("  install Ollama and configure the models for you.\n");
        printf("========================================================\n\n");
        char auto_cmd[MAX_PATH * 3];
        snprintf(auto_cmd, sizeof(auto_cmd), "\"%s\" -m privearch.models.engine_installer --auto", python_path);
        system(auto_cmd);
        return;
    }

    printf("[INFO] Starting local Ollama service in background...\n");
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    char cmd[MAX_PATH + 32];
    snprintf(cmd, sizeof(cmd), "\"%s\" serve", ollama_path);

    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        for (int i = 0; i < 10; i++) {
            Sleep(500);
            if (is_port_listening(11434)) break;
        }
    }
}

static void get_app_dir(char *out_dir, size_t max_len) {
    char exe_path[MAX_PATH];
    GetModuleFileNameA(NULL, exe_path, MAX_PATH);
    char *last_slash = strrchr(exe_path, '\\');
    if (last_slash) {
        *last_slash = '\0';
        strncpy(out_dir, exe_path, max_len);
    } else {
        strcpy(out_dir, ".");
    }
}

static DWORD WINAPI open_browser_thread(LPVOID param) {
    // Wait briefly for Gradio server to listen
    for (int i = 0; i < 20; i++) {
        Sleep(500);
        if (is_port_listening(7860) || is_port_listening(7861)) {
            ShellExecuteA(NULL, "open", DEFAULT_URL, NULL, NULL, SW_SHOWNORMAL);
            return 0;
        }
    }
    ShellExecuteA(NULL, "open", DEFAULT_URL, NULL, NULL, SW_SHOWNORMAL);
    return 0;
}

int main(int argc, char *argv[]) {
    set_console_utf8();
    SetConsoleTitleA("Privearch OS - Zero-Trust Scientific Synthesis");

    char app_dir[MAX_PATH];
    get_app_dir(app_dir, sizeof(app_dir));
    SetCurrentDirectoryA(app_dir);

    char python_path[MAX_PATH];
    find_python(python_path, sizeof(python_path));

    ensure_ollama_running(python_path);

    int mode_cli = 0;
    int mode_vault = 0;
    int mode_update = 0;
    int mode_engine = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--cli") == 0 || strcmp(argv[i], "-c") == 0) {
            mode_cli = 1;
        } else if (strcmp(argv[i], "--vault") == 0 || strcmp(argv[i], "-v") == 0) {
            mode_vault = 1;
        } else if (strcmp(argv[i], "--update") == 0 || strcmp(argv[i], "-u") == 0) {
            mode_update = 1;
        } else if (strcmp(argv[i], "--engine") == 0 || strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--setup-engine") == 0) {
            mode_engine = 1;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("\n========================================================\n");
            printf("  ⚡ PRIVEARCH OPERATING SYSTEM LAUNCHER\n");
            printf("========================================================\n");
            printf("Usage: Privearch.exe [options]\n\n");
            printf("Options:\n");
            printf("  (none)       Launch Modern Web Dashboard (Default)\n");
            printf("  --cli,    -c Launch Interactive Rich Terminal OS\n");
            printf("  --engine, -e Setup/Install Local AI Engine & Models\n");
            printf("  --vault,  -v Re-index all scientific PDFs into Vault\n");
            printf("  --update, -u Over-The-Air (OTA) System Updater\n");
            printf("  --help,   -h Show this help dialog\n\n");
            return 0;
        }
    }

    char target_script[MAX_PATH];
    char command_line[MAX_PATH * 3];

    if (mode_cli) {
        snprintf(target_script, sizeof(target_script), "run_privearch.py");
        snprintf(command_line, sizeof(command_line), "\"%s\" \"%s\\%s\"", python_path, app_dir, target_script);
    } else if (mode_vault) {
        snprintf(target_script, sizeof(target_script), "deploy_chemistry_vault.py");
        snprintf(command_line, sizeof(command_line), "\"%s\" \"%s\\%s\"", python_path, app_dir, target_script);
    } else if (mode_update) {
        snprintf(target_script, sizeof(target_script), "privearch.updater");
        snprintf(command_line, sizeof(command_line), "\"%s\" -m privearch.updater", python_path);
    } else if (mode_engine) {
        snprintf(target_script, sizeof(target_script), "privearch.models.engine_installer");
        snprintf(command_line, sizeof(command_line), "\"%s\" -m privearch.models.engine_installer", python_path);
    } else {
        snprintf(target_script, sizeof(target_script), "run_web.py");
        snprintf(command_line, sizeof(command_line), "\"%s\" \"%s\\%s\"", python_path, app_dir, target_script);
        CreateThread(NULL, 0, open_browser_thread, NULL, 0, NULL);
    }

    // Pass additional arguments if any
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--cli") == 0 || strcmp(argv[i], "-c") == 0) continue;
        if (strcmp(argv[i], "--vault") == 0 || strcmp(argv[i], "-v") == 0) continue;
        if (strcmp(argv[i], "--update") == 0 || strcmp(argv[i], "-u") == 0) continue;
        if (strcmp(argv[i], "--engine") == 0 || strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--setup-engine") == 0) continue;
        if (strcmp(argv[i], "--web") == 0 || strcmp(argv[i], "-w") == 0) continue;
        strncat(command_line, " ", sizeof(command_line) - strlen(command_line) - 1);
        strncat(command_line, argv[i], sizeof(command_line) - strlen(command_line) - 1);
    }

    printf("\n========================================================\n");
    printf("  ⚡ PRIVEARCH OPERATING SYSTEM\n");
    printf("  Airgap Mode: ACTIVE (Zero Cloud Compute)\n");
    printf("  Target: %s\n", target_script);
    printf("========================================================\n\n");

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (!CreateProcessA(NULL, command_line, NULL, NULL, TRUE, 0, NULL, app_dir, &si, &pi)) {
        printf("[ERROR] Failed to start Privearch process: Error code %lu\n", GetLastError());
        printf("Command attempted: %s\n", command_line);
        system("pause");
        return 1;
    }

    // Wait for the python process to exit
    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return (int)exit_code;
}
