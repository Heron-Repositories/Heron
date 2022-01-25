using System;
using NetMQ;
using NetMQ.Sockets;

namespace ReqRep
{
    public class Listener
    {
        private readonly string _host;
        private readonly string _port;
        private readonly Action<string> _messageCallback;

        public Listener(string host, string port, Action<string> messageCallback)
        {
            _host = host;
            _port = port;
            _messageCallback = messageCallback;
        }

        public void RequestMessage()
        {
            var messageReceived = false;
            var message = "";
            AsyncIO.ForceDotNet.Force();

            var timeout = new TimeSpan(0, 0, 2);
            using (var socket = new RequestSocket())
            {
                socket.Connect($"tcp://{_host}:{_port}");
                if (socket.TrySendFrame("Hello"))
                {
                    messageReceived = socket.TryReceiveFrameString(timeout, out message);
                }
            }

            NetMQConfig.Cleanup();
            if (!messageReceived)
                message = "Could not receive message from server!";
            _messageCallback(message);
        }
    }
}