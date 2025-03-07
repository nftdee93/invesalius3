#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------
import sys

import wx
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkCoordinate,
    vtkTextActor,
    vtkTextMapper,
    vtkTextProperty,
)

from invesalius.pubsub import pub as Publisher
import invesalius.constants as const
from invesalius.gui.dialogs import ProgressDialog

# If you are frightened by the code bellow, or think it must have been result of
# an identation error, lookup at:
# Closures in Python (pt)
# http://devlog.waltercruz.com/closures
# http://montegasppa.blogspot.com/2007/01/tampinhas.html
# Closures not only in Python (en)
# http://en.wikipedia.org/wiki/Closure_%28computer_science%29
# http://www.ibm.com/developerworks/library/l-prog2.html
# http://jjinux.blogspot.com/2006/10/python-modifying-counter-in-closure.html

def ShowProgress(number_of_filters = 1,
                 dialog_type="GaugeProgress"):
    """
    To use this closure, do something like this:
        UpdateProgress = ShowProgress(NUM_FILTERS)
        UpdateProgress(vtkObject)
    """
    progress = [0]
    last_obj_progress = [0]
    if (dialog_type == "ProgressDialog"):
        try:
            dlg = ProgressDialog(wx.GetApp().GetTopWindow(), 100)
        except (wx._core.PyNoAppError, AttributeError):
            return lambda obj, label: 0


    # when the pipeline is larger than 1, we have to consider this object
    # percentage
    if number_of_filters < 1:
        number_of_filters = 1
    ratio = (100.0 / number_of_filters)

    def UpdateProgress(obj, label=""):
        """
        Show progress on GUI according to pipeline execution.
        """
        # object progress is cummulative and is between 0.0 - 1.0
        # is necessary verify in case is sending the progress
        #represented by number in case multiprocess, not vtk object
        if isinstance(obj, float) or isinstance(obj, int):
            obj_progress = obj
        else:
            obj_progress = obj.GetProgress()

        # as it is cummulative, we need to compute the diference, to be
        # appended on the interface
        if obj_progress < last_obj_progress[0]: # current obj != previous obj
            difference = obj_progress # 0
        else: # current obj == previous obj
            difference = obj_progress - last_obj_progress[0]

        last_obj_progress[0] = obj_progress

        # final progress status value
        progress[0] = progress[0] + ratio*difference
        # Tell GUI to update progress status value
        if (dialog_type == "GaugeProgress"):
            Publisher.sendMessage('Update status in GUI', value=progress[0], label=label)
        else:
            if (progress[0] >= 99.999):
                progress[0] = 100

            if not(dlg.Update(progress[0],label)):
                dlg.Close()

        return progress[0]

    return UpdateProgress

class Text(object):
    def __init__(self):
        self.layer = 99
        self.children = []
        property = vtkTextProperty()
        property.SetFontSize(const.TEXT_SIZE)
        property.SetFontFamilyToArial()
        property.BoldOff()
        property.ItalicOff()
        property.ShadowOn()
        property.SetJustificationToLeft()
        property.SetVerticalJustificationToTop()
        property.SetColor(const.TEXT_COLOUR)
        self.property = property

        mapper = vtkTextMapper()
        mapper.SetTextProperty(property)
        self.mapper = mapper

        actor = vtkActor2D()
        actor.SetMapper(mapper)
        actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        actor.PickableOff()
        self.actor = actor

        self.SetPosition(const.TEXT_POS_LEFT_UP)

    def SetColour(self, colour):
        self.property.SetColor(colour)

    def ShadowOff(self):
        self.property.ShadowOff()

    def BoldOn(self):
        self.property.BoldOn()

    def SetSize(self, size):
        self.property.SetFontSize(size)

    def SetValue(self, value):
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)
            if sys.platform == 'win32':
                value += "" # Otherwise 0 is not shown under win32
        # With some encoding in some dicom fields (like name) raises a
        # UnicodeEncodeError because they have non-ascii characters. To avoid
        # that we encode in utf-8.
        if sys.platform == 'win32':
            self.mapper.SetInput(value.encode("utf-8", errors='replace'))
        else:
            try:
                self.mapper.SetInput(value.encode("latin-1"))
            except(UnicodeEncodeError):
                self.mapper.SetInput(value.encode("utf-8", errors='replace'))

    def GetValue(self):
        return self.mapper.GetInput()

    def SetCoilDistanceValue(self, value):
        #TODO: Not being used anymore. Can be deleted.
        if isinstance(value, int) or isinstance(value, float):
            value = 'Dist: ' + str("{:06.2f}".format(value)) + ' mm'
            if sys.platform == 'win32':
                value += ""  # Otherwise 0 is not shown under win32
                # With some encoding in some dicom fields (like name) raises a
                # UnicodeEncodeError because they have non-ascii characters. To avoid
                # that we encode in utf-8.

        if sys.platform == 'win32':
            self.mapper.SetInput(value.encode("utf-8"))
        else:
            try:
                self.mapper.SetInput(value.encode("latin-1"))
            except(UnicodeEncodeError):
                self.mapper.SetInput(value.encode("utf-8"))

    def SetPosition(self, position):
        self.actor.GetPositionCoordinate().SetValue(position[0],
                                                    position[1])

    def GetPosition(self, position):
        self.actor.GetPositionCoordinate().GetValue()

    def SetJustificationToRight(self):
        self.property.SetJustificationToRight()

    def SetJustificationToCentered(self):
        self.property.SetJustificationToCentered()


    def SetVerticalJustificationToBottom(self):
        self.property.SetVerticalJustificationToBottom()

    def SetVerticalJustificationToCentered(self):
        self.property.SetVerticalJustificationToCentered()

    def Show(self, value=1):
        if value:
            self.actor.VisibilityOn()
        else:
            self.actor.VisibilityOff()

    def Hide(self):
        self.actor.VisibilityOff()

class TextZero(object):
    def __init__(self):
        self.layer = 99
        self.children = []
        property = vtkTextProperty()
        property.SetFontSize(const.TEXT_SIZE_LARGE)
        property.SetFontFamilyToArial()
        property.BoldOn()
        property.ItalicOff()
        #property.ShadowOn()
        property.SetJustificationToLeft()
        property.SetVerticalJustificationToTop()
        property.SetColor(const.TEXT_COLOUR)
        self.property = property

        actor = vtkTextActor()
        actor.GetTextProperty().ShallowCopy(property)
        actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        actor.PickableOff()
        self.actor = actor

        self.text = ''
        self.position = (0, 0)
        self.symbolic_syze = wx.FONTSIZE_MEDIUM
        self.bottom_pos = False
        self.right_pos = False

    def SetColour(self, colour):
        self.property.SetColor(colour)

    def ShadowOff(self):
        self.property.ShadowOff()

    def SetSize(self, size):
        self.property.SetFontSize(size)
        self.actor.GetTextProperty().ShallowCopy(self.property)

    def SetSymbolicSize(self, size):
        self.symbolic_syze = size

    def SetValue(self, value):
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)
            if sys.platform == 'win32':
                value += "" # Otherwise 0 is not shown under win32
        # With some encoding in some dicom fields (like name) raises a
        # UnicodeEncodeError because they have non-ascii characters. To avoid
        # that we encode in utf-8.
        try:
            self.actor.SetInput(value.encode("cp1252"))
        except(UnicodeEncodeError):
            self.actor.SetInput(value.encode("utf-8"))

        self.text = value

    def SetPosition(self, position):
        self.position = position
        self.actor.GetPositionCoordinate().SetValue(position[0],
                                                    position[1])

    def GetPosition(self):
        return self.actor.GetPositionCoordinate().GetValue()

    def SetJustificationToRight(self):
        self.property.SetJustificationToRight()

    def SetJustificationToCentered(self):
        self.property.SetJustificationToCentered()


    def SetVerticalJustificationToBottom(self):
        self.property.SetVerticalJustificationToBottom()

    def SetVerticalJustificationToCentered(self):
        self.property.SetVerticalJustificationToCentered()

    def Show(self, value=1):
        if value:
            self.actor.VisibilityOn()
        else:
            self.actor.VisibilityOff()

    def Hide(self):
        self.actor.VisibilityOff()

    def draw_to_canvas(self, gc, canvas):
        coord = vtkCoordinate()
        coord.SetCoordinateSystemToNormalizedDisplay()
        coord.SetValue(*self.position)
        x, y = coord.GetComputedDisplayValue(canvas.evt_renderer)
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetSymbolicSize(self.symbolic_syze)
        font.Scale(canvas.viewer.GetContentScaleFactor())
        if self.bottom_pos or self.right_pos:
            w, h = canvas.calc_text_size(self.text, font)
            if self.right_pos:
                x -= w
            if self.bottom_pos:
                y += h
        canvas.draw_text(self.text, (x, y), font=font)


def numpy_to_vtkMatrix4x4(affine):
    """
    Convert a numpy 4x4 array to a vtk 4x4 matrix
    :param affine: 4x4 array
    :return: vtkMatrix4x4 object representing the affine
    """
    # test for type and shape of affine matrix
    # assert isinstance(affine, np.ndarray)
    assert affine.shape == (4, 4)

    affine_vtk = vtkMatrix4x4()
    for row in range(0, 4):
        for col in range(0, 4):
            affine_vtk.SetElement(row, col, affine[row, col])

    return affine_vtk
