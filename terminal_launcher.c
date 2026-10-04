/**
 * Privearch Windows Terminal Launcher
 * Compiled into Privearch-Terminal.exe
 */

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#pragma comment(lib, "ws2_32.lib")

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
    }

    strncpy(out_path, "python.exe", max_len);
    return 1;
}

static void ensure_ollama_running(const char *python_path) {
    if (is_port_listening(11434)) return;

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

int main(int argc, char *argv[]) {
    set_console_utf8();
    SetConsoleTitleA("Privearch Terminal OS");

    char app_dir[MAX_PATH];
    get_app_dir(app_dir, sizeof(app_dir));
    SetCurrentDirectoryA(app_dir);

    char python_path[MAX_PATH];
    find_python(python_path, sizeof(python_path));

    ensure_ollama_running(python_path);

    int mode_update = 0;
    int mode_engine = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--update") == 0 || strcmp(argv[i], "-u") == 0) {
            mode_update = 1;
        } else if (strcmp(argv[i], "--engine") == 0 || strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--setup-engine") == 0) {
            mode_engine = 1;
        }
    }

    char command_line[MAX_PATH * 3];
    if (mode_update) {
        snprintf(command_line, sizeof(command_line), "\"%s\" -m privearch.updater", python_path);
    } else if (mode_engine) {
        snprintf(command_line, sizeof(command_line), "\"%s\" -m privearch.models.engine_installer", python_path);
    } else {
        snprintf(command_line, sizeof(command_line), "\"%s\" \"%s\\run_privearch.py\"", python_path, app_dir);
    }

    for (int i = 1; i < argc; i++) {
        if (mode_update && (strcmp(argv[i], "--update") == 0 || strcmp(argv[i], "-u") == 0)) continue;
        if (mode_engine && (strcmp(argv[i], "--engine") == 0 || strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--setup-engine") == 0)) continue;
        strncat(command_line, " ", sizeof(command_line) - strlen(command_line) - 1);
        strncat(command_line, argv[i], sizeof(command_line) - strlen(command_line) - 1);
    }

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (!CreateProcessA(NULL, command_line, NULL, NULL, TRUE, 0, NULL, app_dir, &si, &pi)) {
        printf("[ERROR] Failed to start Privearch Terminal: %lu\n", GetLastError());
        system("pause");
        return 1;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return (int)exit_code;
}
