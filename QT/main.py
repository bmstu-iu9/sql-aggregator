import sys
import typing

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QModelIndex

import design
from multidb.main import ControlCenter
import html


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data=None, header=None):
        super(TableModel, self).__init__()
        self._data = data or []
        self._header = header or []

    def set_data(self, data, header):
        self._data = data
        self._header = header

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data) and len(self._data[0])

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._header[section]
        else:
            return super().headerData(section, orientation, role)


class MultiDBApp(QtWidgets.QMainWindow, design.Ui_MiltiDB):
    ERROR = 0
    DEBUG = 1
    INFO = 2

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.runQuery.clicked.connect(self.run_query)
        self.saveResult.clicked.connect(self.save_result)

        self.control_center = ControlCenter(r'C:\Users\User\PycharmProjects\diplom_2\sql-aggregator\multidb\config.yaml')

        self.model = TableModel()

    def log(self, msg, flag):
        text = self.logInfo.toHtml()

        msg = html.escape(msg)
        msg = msg.replace('\n', '<br>')

        if flag == self.ERROR:
            color = '#EC7063'
        elif flag == self.INFO:
            color = '#1D8348'
        else:
            color = '#ABB2B9'

        msg = '<span style=color:{};>{}</span>'.format(color, msg)

        self.logInfo.setHtml('######################<br>'.join([text, msg]))

    def save_result(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Выберите папку')
        if path:
            try:
                err = self.control_center.save_result(path)
            except Exception as ex:
                err = 'Fatal error save result: {}'.format(str(ex))
            if err:
                self.log(err, self.ERROR)
            else:
                self.log('Successfully. To view the result, use the following query:\n"SELECT * FROM result;"', self.INFO)

    def run_query(self):
        query = self.queryEditor.toPlainText()
        try:
            err, data = self.control_center.execute(query)
        except Exception as ex:
            err = 'Fatal error run query: {}'.format(str(ex))
            data = None
        if data:
            create, select, insert, view, sample = data
            self.model.set_data(*sample)
            self.queryResult.setModel(self.model)
            print('...')
            print('\n'.join(select))
            print('...')
            debug = 'SELECT QUERIES:\n{}\n\nCREATE QUERIES:\n{}\n\nVIEW QUERY:\n{}'.format(
                '\n'.join(select),
                '\n'.join(create),
                view
            )
            self.log(debug, self.DEBUG)
            self.log('Success', self.INFO)

        if err:
            self.log(err, self.ERROR)


def main():
    app = QtWidgets.QApplication(sys.argv)
    windows = MultiDBApp()
    windows.show()
    app.exec_()


if __name__ == '__main__':
    main()
