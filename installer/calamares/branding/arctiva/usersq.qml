// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Tu cuenta» (usersq): nombre, usuario, equipo, contraseña con indicador de fuerza,
// inicio automático y contraseña de administrador (por defecto, la misma).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import io.calamares.core 1.0
import io.calamares.ui 1.0
import "Arctiva.js" as A

Item {
    id: page
    // Se recalcula al cambiar de idioma: Calamares retraduce entonces las etiquetas de los botones.
    // No todos los módulos llaman a onActivate() de la página (keyboardq y summaryq no).
    property string idioma: A.idioma(Qt.locale(), ViewManager.backLabel)

    readonly property var textos: ({
        titulo: { es: "Tu cuenta", ca: "El teu compte", en: "Your account" },
        intro: { es: "Con ella iniciarás sesión y autorizarás los cambios del sistema.",
                 ca: "Amb ell iniciaràs la sessió i autoritzaràs els canvis del sistema.",
                 en: "You will use it to sign in and to approve system changes." },
        nombre: { es: "Tu nombre", ca: "El teu nom", en: "Your name" },
        usuario: { es: "Nombre de usuario", ca: "Nom d'usuari", en: "User name" },
        equipo: { es: "Nombre del equipo", ca: "Nom de l'ordinador", en: "Computer name" },
        clave: { es: "Contraseña", ca: "Contrasenya", en: "Password" },
        repite: { es: "Repite la contraseña", ca: "Repeteix la contrasenya", en: "Repeat the password" },
        buena: { es: "Buena", ca: "Bona", en: "Good" },
        debil: { es: "Débil", ca: "Feble", en: "Weak" },
        noValida: { es: "No válida", ca: "No vàlida", en: "Not valid" },
        autologin: { es: "Iniciar sesión sin pedir la contraseña", ca: "Inicia la sessió sense demanar la contrasenya", en: "Sign in without asking for the password" },
        misma: { es: "Usar la misma contraseña para administrar el equipo", ca: "Fes servir la mateixa contrasenya per administrar l'ordinador", en: "Use the same password to administer the computer" },
        claveAdmin: { es: "Contraseña de administración", ca: "Contrasenya d'administració", en: "Administrator password" },
        repiteAdmin: { es: "Repite la contraseña de administración", ca: "Repeteix la contrasenya d'administració", en: "Repeat the administrator password" }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    // Etiqueta, campo y mensaje de error debajo (el que da Calamares, ya traducido).
    component Campo: ColumnLayout {
        property alias etiqueta: etiqueta.text
        property alias campo: entrada
        property string estado: ""
        property alias secreto: entrada.echoMode
        signal editado(string texto)

        Layout.fillWidth: true
        spacing: 4
        Label { id: etiqueta; font.bold: true; color: A.texto }
        TextField {
            id: entrada
            Layout.fillWidth: true
            onTextEdited: parent.editado(text)
        }
        Label {
            Layout.fillWidth: true
            visible: parent.estado !== ""
            text: parent.estado
            color: A.error
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
    }

    // Validez: 0 buena, 1 débil, 2 no válida (Config::PasswordValidity).
    component Fuerza: RowLayout {
        property int validez: 2
        property string mensaje: ""
        property bool vacia: true
        visible: !vacia
        spacing: 8
        Label {
            text: parent.validez === 0 ? "✓ " + page.t("buena")
                : parent.validez === 1 ? "! " + page.t("debil")
                : "✕ " + page.t("noValida")
            font.bold: true
            color: parent.validez === 0 ? A.ok : parent.validez === 1 ? A.aviso : A.error
        }
        Label {
            Layout.fillWidth: true
            // Con una contraseña buena Calamares solo dice «OK!».
            visible: parent.validez !== 0
            text: parent.mensaje
            color: A.secundario
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
    }

    Rectangle { anchors.fill: parent; color: A.fondo }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 16

            Cabecera {
                titulo: page.t("titulo")
                intro: page.t("intro")
            }

            Tarjeta {
                Campo {
                    etiqueta: page.t("nombre")
                    campo.text: config.fullName
                    onEditado: (texto) => config.fullName = texto
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Campo {
                        etiqueta: page.t("usuario")
                        campo.text: config.loginName
                        estado: config.loginNameStatus
                        onEditado: (texto) => config.loginName = texto
                    }
                    // usersq.conf siempre escribe el nombre (hostname.location: EtcFile).
                    Campo {
                        etiqueta: page.t("equipo")
                        campo.text: config.hostname
                        estado: config.hostnameStatus
                        onEditado: (texto) => config.hostname = texto
                    }
                }
            }

            Tarjeta {
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Campo {
                        etiqueta: page.t("clave")
                        secreto: TextInput.Password
                        campo.text: config.userPassword
                        onEditado: (texto) => config.userPassword = texto
                    }
                    Campo {
                        etiqueta: page.t("repite")
                        secreto: TextInput.Password
                        campo.text: config.userPasswordSecondary
                        onEditado: (texto) => config.userPasswordSecondary = texto
                    }
                }
                Fuerza {
                    vacia: config.userPassword === ""
                    validez: config.userPasswordValidity
                    mensaje: config.userPasswordMessage
                }

                CheckBox {
                    text: page.t("autologin")
                    checked: config.doAutoLogin
                    onToggled: config.doAutoLogin = checked
                }
                CheckBox {
                    id: misma
                    visible: config.writeRootPassword
                    text: page.t("misma")
                    checked: config.reuseUserPasswordForRoot
                    onToggled: config.reuseUserPasswordForRoot = checked
                }
            }

            Tarjeta {
                visible: config.writeRootPassword && !config.reuseUserPasswordForRoot
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Campo {
                        etiqueta: page.t("claveAdmin")
                        secreto: TextInput.Password
                        campo.text: config.rootPassword
                        onEditado: (texto) => config.rootPassword = texto
                    }
                    Campo {
                        etiqueta: page.t("repiteAdmin")
                        secreto: TextInput.Password
                        campo.text: config.rootPasswordSecondary
                        onEditado: (texto) => config.rootPasswordSecondary = texto
                    }
                }
                Fuerza {
                    vacia: config.rootPassword === ""
                    validez: config.rootPasswordValidity
                    mensaje: config.rootPasswordMessage
                }
            }
        }
    }
}
