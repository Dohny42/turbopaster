import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: palette
    objectName: "searchPalette"
    required property var searchController
    visible: true
    width: 680
    height: 104 + resultsPanel.height
    minimumWidth: 420
    maximumWidth: 900
    flags: Qt.FramelessWindowHint | Qt.Tool
    color: "transparent"
    property bool animationsEnabled: true

    onActiveChanged: {
        if (active)
            searchInput.forceActiveFocus()
    }

    Rectangle {
        anchors.fill: parent
        radius: 10
        color: "#141b18"
        border.color: "#35433c"
        border.width: 1

        Column {
            id: content
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8

            TextField {
                id: searchInput
                objectName: "searchInput"
                width: parent.width
                height: 54
                placeholderText: "Search snippets"
                placeholderTextColor: "#8d9a91"
                color: "#f0f5ef"
                selectionColor: "#299fe8"
                selectedTextColor: "#172018"
                leftPadding: 18
                rightPadding: 18
                font.pixelSize: 18
                font.family: "Segoe UI"
                selectByMouse: true
                background: Rectangle {
                    radius: 6
                    color: "#202a25"
                    border.width: 1
                    border.color: searchInput.activeFocus ? "#299fe8" : "#394940"
                }

                onTextChanged: palette.searchController.search(text)
                Keys.onPressed: function(event) {
                    if (event.key === Qt.Key_Down) {
                        if (resultsList.count > 0)
                            resultsList.currentIndex = Math.min(resultsList.currentIndex + 1, resultsList.count - 1)
                        event.accepted = true
                    } else if (event.key === Qt.Key_Up) {
                        if (resultsList.count > 0)
                            resultsList.currentIndex = Math.max(resultsList.currentIndex - 1, 0)
                        event.accepted = true
                    } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                        if (resultsList.count > 0)
                            palette.searchController.choose(palette.searchController.results[resultsList.currentIndex].name)
                        event.accepted = true
                    } else if (event.key === Qt.Key_Escape) {
                        palette.close()
                        event.accepted = true
                    }
                }

                Component.onCompleted: forceActiveFocus()
            }

            Item {
                id: resultsPanel
                objectName: "resultsPanel"
                width: parent.width
                height: searchInput.text.length === 0 ? 0 :
                    (palette.searchController.results.length === 0 ? 42 : Math.min(palette.searchController.results.length, 6) * 66)
                clip: true

                Behavior on height {
                    enabled: palette.animationsEnabled
                    NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                }

                ListView {
                    id: resultsList
                    objectName: "resultsList"
                    anchors.fill: parent
                    model: palette.searchController.results
                    visible: count > 0
                    currentIndex: count > 0 ? 0 : -1
                    clip: true
                    spacing: 2
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        required property var modelData
                        width: resultsList.width
                        height: 64
                        radius: 5
                        color: ListView.isCurrentItem ? "#29382f" : "transparent"

                        Column {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 3

                            Text {
                                width: parent.width
                                text: modelData.name
                                color: ListView.isCurrentItem ? "#299fe8" : "#e7eee8"
                                font.pixelSize: 15
                                font.bold: true
                                font.family: "Segoe UI"
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }

                            Text {
                                objectName: "previewText"
                                width: parent.width
                                text: modelData.preview
                                color: "#9daaa1"
                                font.pixelSize: 11
                                font.family: "Segoe UI"
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }

                        TapHandler {
                            onTapped: {
                                resultsList.currentIndex = index
                                palette.searchController.choose(modelData.name)
                            }
                        }
                    }
                }

                Text {
                    anchors.fill: parent
                    visible: searchInput.text.length > 0 && palette.searchController.results.length === 0
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 14
                    text: "No matching snippets"
                    color: "#8d9a91"
                    font.pixelSize: 13
                    font.family: "Segoe UI"
                }
            }
        }
    }

    Connections {
        target: palette.searchController
        function onChosen() {
            palette.close()
        }
    }
}