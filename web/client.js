var pc = null;

function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });
    return pc.createOffer().then((offer) => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        // wait for ICE gathering to complete
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then((response) => {
        return response.text().then((text) => {
            var data;
            try { data = text ? JSON.parse(text) : {}; } catch (_) { throw new Error('Server returned non-JSON. Check Network tab.'); }
            if (!response.ok || data.error) {
                throw new Error(data.error || ('Connection failed (' + response.status + ')'));
            }
            return data;
        });
    }).then((answer) => {
        document.getElementById('sessionid').value = answer.sessionid
        return pc.setRemoteDescription(answer);
    }).catch((e) => {
        document.getElementById('start').style.display = 'inline-block';
        document.getElementById('stop').style.display = 'none';
        if (pc) { pc.close(); pc = null; }
        var msg = e.message || String(e);
        if (msg === 'Failed to fetch' || (e.name && e.name === 'TypeError')) {
            msg = 'Cannot reach server. Start it with: ./run_local_test.sh (or ./run_local.sh if you have model files).';
        }
        alert(msg);
    });
}

function start() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    if (document.getElementById('use-stun').checked) {
        config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];
    }

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', (evt) => {
        var stream = evt.streams[0] || new MediaStream([evt.track]);
        if (evt.track.kind == 'video') {
            var video = document.getElementById('video');
            video.srcObject = stream;
            video.muted = true;  // required for autoplay in most browsers
            video.play().catch(function(e) { console.warn('Video play:', e); });
        } else {
            document.getElementById('audio').srcObject = stream;
        }
    });

    document.getElementById('start').style.display = 'none';
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';

    // close peer connection
    setTimeout(() => {
        pc.close();
    }, 500);
}

window.onunload = function(event) {
    // 在这里执行你想要的操作
    setTimeout(() => {
        pc.close();
    }, 500);
};

window.onbeforeunload = function (e) {
        setTimeout(() => {
                pc.close();
            }, 500);
        e = e || window.event
        // 兼容IE8和Firefox 4之前的版本
        if (e) {
          e.returnValue = '关闭提示'
        }
        // Chrome, Safari, Firefox 4+, Opera 12+ , IE 9+
        return '关闭提示'
      }