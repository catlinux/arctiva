// SPDX-License-Identifier: GPL-3.0-or-later
// Barra inferior con la cola de instalaciones: visible desde cualquier módulo mientras haya algo
// en cola, en curso o recién terminado.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

QQC2.ToolBar {
    id: bar

    readonly property var progress: appsBackend.queueProgress
    readonly property var items: appsBackend.queue
    readonly property int failed: items.filter(i => i.state === "failed").length
    signal detailsRequested()

    visible: items.length > 0
    position: QQC2.ToolBar.Footer

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        QQC2.BusyIndicator {
            visible: bar.progress.active === true
            running: visible
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
        }
        Kirigami.Icon {
            visible: bar.progress.active !== true
            source: bar.failed > 0 ? "dialog-warning" : "dialog-ok-apply"
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            QQC2.Label {
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: bar.progress.active === true
                    ? (bar.progress.action === "remove"
                        ? qsTr("Removing %1 (%2 of %3)")
                        : qsTr("Installing %1 (%2 of %3)")).arg(bar.progress.name).arg(bar.progress.position).arg(bar.progress.total)
                    : bar.failed > 0 ? qsTr("Queue finished with %1 error(s)").arg(bar.failed)
                    : qsTr("Queue finished")
            }
            QQC2.ProgressBar {
                visible: bar.progress.active === true
                Layout.fillWidth: true
                indeterminate: bar.progress.fraction < 0
                from: 0
                to: 1
                value: bar.progress.fraction < 0 ? 0 : bar.progress.fraction
            }
        }

        QQC2.Button {
            text: qsTr("Details")
            icon.name: "view-list-details"
            onClicked: bar.detailsRequested()
        }
        QQC2.Button {
            visible: bar.progress.active !== true
            text: qsTr("Dismiss")
            icon.name: "dialog-close"
            onClicked: appsBackend.clearFinished()
        }
    }
}
