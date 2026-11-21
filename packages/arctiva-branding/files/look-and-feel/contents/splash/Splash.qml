// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Rectangle {
    id: root
    color: "#04060c"
    property int stage: 0

    onStageChanged: if (stage >= 2) logo.opacity = 1

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#04060c" }
            GradientStop { position: 1.0; color: "#0b1a4a" }
        }
    }

    Image {
        id: logo
        anchors.centerIn: parent
        height: parent.height * 0.22
        fillMode: Image.PreserveAspectFit
        source: "images/arctiva.svg"
        sourceSize.height: height
        opacity: 0
        Behavior on opacity { NumberAnimation { duration: 700; easing.type: Easing.InOutQuad } }
    }

    // Arco del anillo girando, como el indicador de arranque.
    Canvas {
        id: spinner
        width: root.height * 0.07
        height: width
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: logo.bottom
        anchors.topMargin: root.height * 0.06
        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();
            ctx.lineWidth = width * 0.1;
            ctx.strokeStyle = "#1d2a4d";
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, width / 2 - ctx.lineWidth, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.strokeStyle = "#6fd6ff";
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, width / 2 - ctx.lineWidth, 0, Math.PI * 0.6);
            ctx.stroke();
        }
        RotationAnimator on rotation { from: 0; to: 360; duration: 1100; loops: Animation.Infinite; running: true }
    }
}
