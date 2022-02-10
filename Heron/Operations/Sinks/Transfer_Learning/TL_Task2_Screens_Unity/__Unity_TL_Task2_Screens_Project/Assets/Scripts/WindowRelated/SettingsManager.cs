using System.Collections;
using System.Collections.Generic;
using UnityEngine;

#if UNITY_STANDALONE_WIN
 
using System;
using System.Runtime.InteropServices;
 
#endif



public class SettingsManager : MonoBehaviour
{

    public bool fullScreen = false;
    private static string fullScreenKey = "Full Screen";

    public int windowPositionX = 1000;
    public int windowPositionY = 0;
    public int monitorWidth = 1000;
    public int monitorHeight = 800;

    

#if UNITY_STANDALONE_WIN
   
    [DllImport("user32.dll", EntryPoint = "SetWindowPos")]
    private static extern bool SetWindowPos(IntPtr hwnd, int hWndInsertAfter, int X, int Y, int cx, int cy, int uFlags);
   
    [DllImport("user32.dll", EntryPoint = "FindWindow")]
    public static extern IntPtr FindWindow(string className, string windowName);
   
    public static IEnumerator SetWindowPosition(int x, int y) {
        yield return new WaitForEndOfFrame();
        yield return new WaitForEndOfFrame();
        SetWindowPos(FindWindow(null, Application.productName), 0, x, y, 0, 0, 5);
    }
   
#endif

    void Start()
    {
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = 15;

        CheckAndSet();
    }

    private void CheckAndSet()
    {
        if (PlayerPrefs.GetInt(fullScreenKey, 0) >= 1)
        {
            SetFullScreen();
        }
        else
        {
            SetWindowed();
        }
    }

    public void SetFullScreen()
    {
        Screen.SetResolution(monitorWidth, monitorHeight, true);
        fullScreen = true;
        PlayerPrefs.SetInt(fullScreenKey, 1);
        PlayerPrefs.Save();
    }

    public void SetWindowed()
    {
        SetWindowResolution();
        
        fullScreen = false;
        PlayerPrefs.SetInt(fullScreenKey, 0);
        PlayerPrefs.Save();
    }

    private void SetWindowResolution()
    {
        

#if UNITY_STANDALONE_WIN
       Screen.SetResolution(monitorWidth, monitorHeight, false);
        //int x = monitorWidth / 2;
        //x -= size / 2;
        //int y = monitorHeight / 2;
        //y -= size / 2;
        //StartCoroutine(SetWindowPosition(x, y));
        StartCoroutine(SetWindowPosition(windowPositionX, windowPositionY));
       
#endif
    }
}
