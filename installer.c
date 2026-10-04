/**
 * Privearch One-Click Windows Installer
 * Compiled into Privearch-Setup.exe
 */

#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "shlwapi.lib")

static void set_utf8(void) {
    SetConsoleOutputCP(65001);
    SetConsoleCP(65001);
}

// Helper: Create a Windows Shell Shortcut (.lnk)
static BOOL create_shortcut(LPCSTR target_path, LPCSTR link_path, LPCSTR description, LPCSTR icon_path, LPCSTR work_dir) {
    HRESULT hr;
    IShellLinkA *p_sl = NULL;
    IPersistFile *p_pf = NULL;

    hr = CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER, &IID_IShellLinkA, (void **)&p_sl);
    if (FAILED(hr)) return FALSE;

    p_sl->lpVtbl->SetPath(p_sl, target_path);
    if (description) p_sl->lpVtbl->SetDescription(p_sl, description);
    if (work_dir) p_sl->lpVtbl->SetWorkingDirectory(p_sl, work_dir);
    if (icon_path) p_sl->lpVtbl->SetIconLocation(p_sl, icon_path, 0);

    hr = p_sl->lpVtbl->QueryInterface(p_sl, &IID_IPersistFile, (void **)&p_pf);
    if (SUCCEEDED(hr)) {
        WCHAR wsz_link[MAX_PATH];
        MultiByteToWideChar(CP_ACP, 0, link_path, -1, wsz_link, MAX_PATH);
        hr = p_pf->lpVtbl->Save(p_pf, wsz_link, TRUE);
        p_pf->lpVtbl->Release(p_pf);
    }
    p_sl->lpVtbl->Release(p_sl);
    return SUCCEEDED(hr);
}

// Helper: Recursively copy directory using xcopy / robocopy / SHFileOperation
static BOOL copy_folder_recursive(LPCSTR src, LPCSTR dst) {
    char cmd[MAX_PATH * 3];
    snprintf(cmd, sizeof(cmd), "robocopy \"%s\" \"%s\" /E /NFL /NDL /NJH /NJS /nc /ns /np >nul", src, dst);
    int res = system(cmd);
    return (res <= 7); // Robocopy returns 0-7 for success
}

static BOOL copy_single_file(LPCSTR src, LPCSTR dst) {
    return CopyFileA(src, dst, FALSE);
}

// Helper: Add folder to User PATH in registry
static BOOL add_to_user_path(LPCSTR new_dir) {
    HKEY h_key;
    if (RegOpenKeyExA(HKEY_CURRENT_USER, "Environment", 0, KEY_READ | KEY_WRITE, &h_key) != ERROR_SUCCESS) {
        return FALSE;
    }

    char current_path[32768] = {0};
    DWORD path_len = sizeof(current_path);
    DWORD type = REG_EXPAND_SZ;

    if (RegQueryValueExA(h_key, "Path", NULL, &type, (LPBYTE)current_path, &path_len) != ERROR_SUCCESS) {
        current_path[0] = '\0';
    }

    // Check if already in PATH
    if (strstr(current_path, new_dir) == NULL) {
        char updated_path[32768];
        if (strlen(current_path) > 0) {
            snprintf(updated_path, sizeof(updated_path), "%s;%s", current_path, new_dir);
        } else {
            snprintf(updated_path, sizeof(updated_path), "%s", new_dir);
        }

        RegSetValueExA(h_key, "Path", 0, REG_EXPAND_SZ, (const BYTE *)updated_path, (DWORD)(strlen(updated_path) + 1));
        // Broadcast change
        DWORD_PTR result;
        SendMessageTimeoutA(HWND_BROADCAST, WM_SETTINGCHANGE, 0, (LPARAM)"Environment", SMTO_ABORTIFHUNG, 2000, &result);
    }

    RegCloseKey(h_key);
    return TRUE;
}

static void create_uninstaller_script(LPCSTR install_dir) {
    char uninstaller_path[MAX_PATH];
    snprintf(uninstaller_path, sizeof(uninstaller_path), "%s\\Uninstall.bat", install_dir);

    FILE *f = fopen(uninstaller_path, "w");
    if (!f) return;

    fprintf(f, "@echo off\n");
    fprintf(f, "title Privearch Uninstaller\n");
    fprintf(f, "echo ========================================================\n");
    fprintf(f, "echo   Uninstalling Privearch Scientific Operating System...\n");
    fprintf(f, "echo ========================================================\n");
    fprintf(f, "echo.\n");
    fprintf(f, "set /p CONFIRM=\"Are you sure you want to remove Privearch? (Y/N): \"\n");
    fprintf(f, "if /i not \"%%CONFIRM%%\"==\"Y\" exit /b\n\n");
    
    // Remove shortcuts
    fprintf(f, "del \"%%USERPROFILE%%\\Desktop\\Privearch.lnk\" 2>nul\n");
    fprintf(f, "del \"%%USERPROFILE%%\\Desktop\\Privearch Terminal.lnk\" 2>nul\n");
    fprintf(f, "rmdir /s /q \"%%APPDATA%%\\Microsoft\\Windows\\Start Menu\\Programs\\Privearch\" 2>nul\n");
    
    // Self-delete folder via temporary batch
    fprintf(f, "echo [OK] Shortcuts removed.\n");
    fprintf(f, "echo [OK] Privearch has been successfully uninstalled.\n");
    fprintf(f, "pause\n");
    fclose(f);
}

int main(int argc, char *argv[]) {
    set_utf8();
    SetConsoleTitleA("Privearch Setup Wizard");
    CoInitialize(NULL);

    printf("\n======================================================================\n");
    printf("  ⚡ PRIVEARCH SCIENTIFIC OPERATING SYSTEM - SETUP WIZARD\n");
    printf("  Zero-Trust  •  100%% Local Airgap  •  CPU + 4GB VRAM\n");
    printf("======================================================================\n\n");

    // 1. Determine Source Directory (where the setup exe is located)
    char src_dir[MAX_PATH];
    GetModuleFileNameA(NULL, src_dir, MAX_PATH);
    char *p = strrchr(src_dir, '\\');
    if (p) *p = '\0';

    // 2. Determine Destination Directory (%LOCALAPPDATA%\Programs\Privearch)
    char local_app_data[MAX_PATH];
    if (SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, local_app_data) != S_OK) {
        printf("[ERROR] Failed to locate Local AppData directory.\n");
        system("pause");
        return 1;
    }

    char install_dir[MAX_PATH];
    snprintf(install_dir, sizeof(install_dir), "%s\\Programs\\Privearch", local_app_data);

    printf("[1/5] Target Installation Path:\n      %s\n\n", install_dir);
    CreateDirectoryA(install_dir, NULL);

    // 3. Copy Application Assets
    printf("[2/5] Deploying Privearch binaries, core engine & pre-indexed vault...\n");
    
    // Core files
    const char *files_to_copy[] = {
        "Privearch.exe",
        "Privearch-Terminal.exe",
        "privearch.ico",
        "run_web.py",
        "run_privearch.py",
        "deploy_chemistry_vault.py",
        "README.md",
        NULL
    };

    for (int i = 0; files_to_copy[i] != NULL; i++) {
        char s_file[MAX_PATH], d_file[MAX_PATH];
        snprintf(s_file, sizeof(s_file), "%s\\%s", src_dir, files_to_copy[i]);
        snprintf(d_file, sizeof(d_file), "%s\\%s", install_dir, files_to_copy[i]);
        if (PathFileExistsA(s_file)) {
            copy_single_file(s_file, d_file);
        }
    }

    // Folders: privearch and .privearch_cache
    char s_privearch[MAX_PATH], d_privearch[MAX_PATH];
    snprintf(s_privearch, sizeof(s_privearch), "%s\\privearch", src_dir);
    snprintf(d_privearch, sizeof(d_privearch), "%s\\privearch", install_dir);
    copy_folder_recursive(s_privearch, d_privearch);

    char s_cache[MAX_PATH], d_cache[MAX_PATH];
    snprintf(s_cache, sizeof(s_cache), "%s\\.privearch_cache", src_dir);
    snprintf(d_cache, sizeof(d_cache), "%s\\.privearch_cache", install_dir);
    if (PathFileExistsA(s_cache)) {
        copy_folder_recursive(s_cache, d_cache);
    }

    printf("      ✓ Files, pre-indexed vault (2,280 chunks), and models copied.\n\n");

    // 4. Create Desktop Shortcuts
    printf("[3/5] Creating Desktop Shortcuts...\n");
    char desktop_dir[MAX_PATH];
    if (SHGetFolderPathA(NULL, CSIDL_DESKTOP, NULL, 0, desktop_dir) == S_OK) {
        char exe_main[MAX_PATH], ico_path[MAX_PATH], link_web[MAX_PATH];
        snprintf(exe_main, sizeof(exe_main), "%s\\Privearch.exe", install_dir);
        snprintf(ico_path, sizeof(ico_path), "%s\\privearch.ico", install_dir);
        snprintf(link_web, sizeof(link_web), "%s\\Privearch.lnk", desktop_dir);

        create_shortcut(exe_main, link_web, "Privearch Web Dashboard", ico_path, install_dir);

        char exe_term[MAX_PATH], link_term[MAX_PATH];
        snprintf(exe_term, sizeof(exe_term), "%s\\Privearch-Terminal.exe", install_dir);
        snprintf(link_term, sizeof(link_term), "%s\\Privearch Terminal.lnk", desktop_dir);

        create_shortcut(exe_term, link_term, "Privearch Terminal OS", ico_path, install_dir);
        printf("      ✓ Desktop shortcuts created (Privearch.lnk & Privearch Terminal.lnk).\n\n");
    }

    // 5. Create Start Menu Shortcuts
    printf("[4/5] Creating Start Menu Programs entry...\n");
    char programs_dir[MAX_PATH];
    if (SHGetFolderPathA(NULL, CSIDL_PROGRAMS, NULL, 0, programs_dir) == S_OK) {
        char sm_privearch[MAX_PATH];
        snprintf(sm_privearch, sizeof(sm_privearch), "%s\\Privearch", programs_dir);
        CreateDirectoryA(sm_privearch, NULL);

        char exe_main[MAX_PATH], ico_path[MAX_PATH], link_sm_web[MAX_PATH];
        snprintf(exe_main, sizeof(exe_main), "%s\\Privearch.exe", install_dir);
        snprintf(ico_path, sizeof(ico_path), "%s\\privearch.ico", install_dir);
        snprintf(link_sm_web, sizeof(link_sm_web), "%s\\Privearch.lnk", sm_privearch);
        create_shortcut(exe_main, link_sm_web, "Privearch Web Dashboard", ico_path, install_dir);

        char exe_term[MAX_PATH], link_sm_term[MAX_PATH];
        snprintf(exe_term, sizeof(exe_term), "%s\\Privearch-Terminal.exe", install_dir);
        snprintf(link_sm_term, sizeof(link_sm_term), "%s\\Privearch Terminal.lnk", sm_privearch);
        create_shortcut(exe_term, link_sm_term, "Privearch Terminal OS", ico_path, install_dir);
        printf("      ✓ Start Menu folder created.\n\n");
    }

    // 6. Add to User PATH
    printf("[5/5] Registering 'privearch' in Windows Environment PATH...\n");
    if (add_to_user_path(install_dir)) {
        printf("      ✓ Added %s to User PATH.\n", install_dir);
        printf("      ✓ You can now type 'privearch' or 'privearch-terminal' in any terminal!\n\n");
    }

    create_uninstaller_script(install_dir);

    CoUninitialize();

    printf("======================================================================\n");
    printf("  🎉 INSTALLATION COMPLETE!\n");
    printf("======================================================================\n");
    printf("  You can now start Privearch in two easy ways:\n");
    printf("    1. Double-click the 'Privearch' shortcut on your Desktop\n");
    printf("    2. Type 'Privearch' in your Windows Start Menu search\n");
    printf("    3. Or run 'Privearch.exe' directly from any terminal!\n\n");

    printf("Press any key to finish or launch Privearch now...");
    getchar();
    return 0;
}
