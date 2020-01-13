#!/usr/bin/env python3
import random
import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.config import Config
from kivy.clock import Clock
from kivy.animation import Animation


Config.set("graphics", "width", "1080")
Config.set("graphics", "height", "2160")
#Config.set("graphics", "width", "500")
#Config.set("graphics", "height", "1000")
# 36 = 6x6 or 4x9 or 3x12 or 2x18

ICONS = {
    "M": "data/mill.png",
    "E": "data/goodyear.png",
    "R": "data/robber.png",
    "T": "data/joust.png",
    "?": "data/event.png",
    "1": "data/dice1.png",
    "2": "data/dice2.png",
    "3": "data/dice3.png",
    "4": "data/dice4.png",
    "5": "data/dice5.png",
    "6": "data/dice6.png",
}

kv = """
<SelectableLabel>:
    font_size: "60sp"
    color: (1, 0, 0, 1)
    bg_color: (1, 1, 1, 0.15)
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            source: self.source
            pos: self.pos
            size: self.size

<MainScreen>
    BoxLayout:
        orientation: "vertical"
        CardSelector:
            is_event_stack: False
            viewclass: "SelectableLabel"
            id: number_die
            SelectableRecycleGridLayout:
                spacing: 7
                cols: 6
                rows: 6
                default_size_hint: 1/6, 1/6
                orientation: "vertical"
                multiselect: False
                touch_multiselect: False
        AnchorLayout:
            size_hint_y: 0.15
            Button:
                id: reveal_button
                anchor_x: "center"
                anchor_y: "center"
                size_hint_x: .45
                size_hint_y: .8
                text: "aufdecken"
                font_size: "32sp"
                disabled: not app.valid_selection
                on_press: app.reveal_cards()
        CardSelector:
            is_event_stack: True
            viewclass: "SelectableLabel"
            id: event_die
            SelectableRecycleGridLayout:
                spacing: 7
                cols: 6
                rows: 6
                default_size_hint: 1/6, 1/6
                orientation: "vertical"
                multiselect: False
                touch_multiselect: False
    """


class MainScreen(Screen):
    pass


class SelectableRecycleGridLayout(FocusBehavior,
                                  LayoutSelectionBehavior,
                                  RecycleGridLayout):
    pass


class TestApp(App):
    valid_selection = BooleanProperty(False)

    def build(self):
        Builder.load_string(kv)
        self.manager = ScreenManager(transition=SlideTransition())
        self.main = MainScreen(name="main")
        self.manager.add_widget(self.main)
        self.number_die = self.main.ids.number_die
        self.event_die = self.main.ids.event_die
        return self.manager

    def evaluate_selection(self):
        try:
            conditions = [hasattr(self.number_die, "selection"),
                          hasattr(self.event_die, "selection"),
                          self.number_die.selection.selected,
                          self.event_die.selection.selected]
            self.valid_selection = all(conditions)
        except AttributeError:
            self.valid_selection = False

    def reveal_cards(self):
        if self.valid_selection:
            self.event_die.reveal_selected_card()
            self.number_die.reveal_selected_card()
            self.main.ids.reveal_button.disabled = True

    def on_pause(self):
        self.valid_selection = False
        return True

    def on_resume(self):
        self.valid_selection = False
        self.main.ids.reveal_button.disabled = True


class CardSelector(RecycleView):
    def __init__(self, **kwargs):
        super(CardSelector, self).__init__(**kwargs)
        Clock.schedule_once(self.prepare_cards, 0)

    def prepare_cards(self, delay=0):
        if self.is_event_stack:
            stack = ["?", "?", "R", "T", "M", "E"] * 6
        else:
            stack = [str(x) for x in list(range(1, 7)) * 6]
        random.shuffle(stack)
        self.data = []
        cards_to_del = random.sample(range(36), 5)
        for i in range(36):
            card_dict = {}
            card_dict["selectable"] = i not in cards_to_del
            card_dict["discarded"] = i in cards_to_del
            card_dict["value"] = stack[i]
            self.data.append(card_dict)

    def reveal_selected_card(self):
        card_value = self.selection.reveal()
        return(card_value)


class SelectableLabel(RecycleDataViewBehavior, Label):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    source = StringProperty("data/card_backside.png")

    def reveal(self):
        self.bg_color = (0, 0, 0, 0)
        anim = Animation(bg_color=(1, 1, 1, 1), t="in_bounce", duration=2)
        self.selectable = False
        self.selected = False
        card_value = self.rv.data[self.index]["value"]
        self.source = ICONS[card_value]
        anim.start(self)
        return(card_value)

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        self.rv = rv
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        """ Add selection on touch down """
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected
        self.selectable = \
            self.selectable and self.rv.data[self.index]["selectable"]
        self.rv.data[self.index]["selectable"] = self.selectable
        if is_selected:
            self.bg_color = (0, .8, .08, .7)
            rv.selection = self
        else:
            if self.selectable:
                self.bg_color = (1, 1, 1, .33)
            elif self.discarded:
                self.bg_color = (1, 1, 1, .15)
            else:
                self.bg_color = (1, 1, 1, .25)
        App.get_running_app().evaluate_selection()


if __name__ == "__main__":
    TestApp().run()
