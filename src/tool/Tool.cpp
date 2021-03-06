#include "Tool.h"
#include <QTextStream>
#include <QFileDialog>
#include <QKeyEvent>
#include <QDebug>
#include <iostream>

namespace tool {

// This file saves the dimensions from the last use of the tool
QFile file(QString("./.geometry"));

Tool::Tool(const char* title) :
    QMainWindow(),
    diagram(),
    selector(),
    logView(this),
    tableCreator(this),
    toolTabs(new QTabWidget),
    toolbar(new QToolBar),
    nextButton(new QPushButton(tr(">"))),
    prevButton(new QPushButton(tr("<"))),
    recordButton(new QPushButton(tr("Rec"))),
    scrollArea(new QScrollArea),
    scrollBarSize(new QSize(5, 35)),
    tabStartSize(new QSize(toolTabs->size()))
{
    // Set up the GUI and slots
    this->setWindowTitle(tr(title));

    //connect both fwd and prv button to the run slot
    connect(nextButton, SIGNAL(clicked()), &diagram, SLOT(runForward()));
    connect(prevButton, SIGNAL(clicked()), &diagram, SLOT(runBackward()));

    connect(&selector, SIGNAL(signalNewDataSet(std::vector<std::string>)),
            &diagram, SLOT(addUnloggers(std::vector<std::string>)));

    connect(&diagram, SIGNAL(signalNewDisplayWidget(QWidget*, std::string)),
            &logView, SLOT(newDisplayWidget(QWidget*, std::string)));

    connect(&diagram, SIGNAL(signalUnloggersReady()),
            this, SLOT(setUpModules()));

    toolbar->addWidget(prevButton);
    toolbar->addWidget(nextButton);
    toolbar->addWidget(recordButton);

    toolTabs->addTab(&selector, tr("Data"));
    toolTabs->addTab(&logView, tr("Log View"));
    toolTabs->addTab(&tableCreator, tr("Color Creator"));

    this->setCentralWidget(toolTabs);
    this->addToolBar(toolbar);

    // Figure out the appropriate dimensions for the window
    if (file.open(QIODevice::ReadWrite)){
            QTextStream in(&file);
            geometry = new QRect(in.readLine().toInt(), in.readLine().toInt(),
                                 in.readLine().toInt(), in.readLine().toInt());
            file.close();
    }
    // If we don't have dimensions, default to hard-coded values
    if((geometry->width() == 0) && (geometry->height() == 0)){
        geometry = new QRect(75, 75, 1132, 958);
    }
    this->setGeometry(*geometry);
}

Tool::~Tool() {
    // Write the current dimensions to the .geometry file for next use
    if (file.open(QIODevice::ReadWrite)){
        QTextStream out(&file);
        out << this->pos().x() << "\n"
            << this->pos().y() << "\n"
            << this->width() << "\n"
            << this->height() << "\n";
    }
}

void Tool::setUpModules()
{
    if (diagram.connectToUnlogger<messages::YUVImage>(tableCreator.topImageIn,
                                                      "top") &&
        diagram.connectToUnlogger<messages::YUVImage>(tableCreator.bottomImageIn,
                                                      "bottom"))
    {
        diagram.addModule(tableCreator);
    }
    else
    {
        std::cout << "Right now you can't use the color table creator without"
                  << " two image logs." << std::endl;
    }
}

// Keyboard control
void Tool::keyPressEvent(QKeyEvent * event)
{
    switch (event->key()) {
    case Qt::Key_N:
        diagram.runForward();
        break;
    case Qt::Key_P:
        diagram.runBackward();
        break;
    default:
        QWidget::keyPressEvent(event);
    }
}

// Provides scrollbars appropriately if the window gets too small
void Tool::resizeEvent(QResizeEvent* ev)
{
    QSize widgetSize = ev->size();
    if((widgetSize.width() > tabStartSize->width()) ||
       (widgetSize.height() > tabStartSize->height())) {
        toolTabs->resize(widgetSize-*scrollBarSize);
    }
    QWidget::resizeEvent(ev);
}

}
