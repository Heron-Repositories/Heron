using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class WriteLogToFile : MonoBehaviour
{
    public bool On;
    string filename = "";

    private void OnEnable()
    {
        if (On)
            Application.logMessageReceived += Log;
    }

    private void OnDisable()
    {   
        if (On)
            Application.logMessageReceived -= Log;
    }

    private void Start()
    {
        filename = Application.dataPath + "/LogFile.txt";
    }

    public void Log(string logString, string stackTrace, LogType type)
    {
        TextWriter tw = new StreamWriter(filename, true);

        tw.WriteLine("[" + System.DateTime.Now + "]" + logString);
        tw.WriteLine(stackTrace);

        tw.Close();
    }
}
