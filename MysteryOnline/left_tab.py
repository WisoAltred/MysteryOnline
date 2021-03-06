from kivy.app import App
from kivy.utils import platform
from kivy.properties import ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.logger import Logger

import MysteryOnline
from MysteryOnline.utils import binary_search
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout


class SectionLabel(Label):

    def __init__(self, section, **kwargs):
        super(SectionLabel, self).__init__(**kwargs)
        self.section = section

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if platform == "win":
                from kivy.input.providers.wm_touch import WM_MotionEvent
                if isinstance(touch, WM_MotionEvent) and touch.is_double_tap:
                    self.on_selected()
                    return True
            if touch.button == 'left' and touch.is_double_tap:
                self.on_selected()
                return True

    def on_selected(self):
        self.section.on_selected(self.parent)


class SubSectionLabel(Label):

    def __init__(self, subsection, **kwargs):
        super(SubSectionLabel, self).__init__(**kwargs)
        self.subsection = subsection

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if platform == "win":
                from kivy.input.providers.wm_touch import WM_MotionEvent
                if isinstance(touch, WM_MotionEvent) and touch.is_double_tap:
                    self.on_selected()
                    return True
            if touch.button == 'left' and touch.is_double_tap:
                self.on_selected()
                return True

    def on_selected(self):
        self.subsection.on_selected(self.parent)


class SubSubSectionLabel(Label):

    def __init__(self, **kwargs):
        super(SubSubSectionLabel, self).__init__(**kwargs)


class TrackLabel(Label):

    def __init__(self, track, **kwargs):
        super(TrackLabel, self).__init__(**kwargs)
        self.track = track

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if platform == "win":
                from kivy.input.providers.wm_touch import WM_MotionEvent
                if isinstance(touch, WM_MotionEvent) and touch.is_double_tap:
                    self.on_selected()
                    return True
            if touch.button == 'left' and touch.is_double_tap:
                self.on_selected()
                return True

    def on_selected(self):
        self.track.on_selected()


class TrackSection:

    def __init__(self, name):
        self.name = name
        self.subsections = []
        self.tracks = []

    def add_subsection(self, subsection):
        self.subsections.append(subsection)

    def add_track(self, track_name):
        self.tracks.append(track_name)

    def get_name(self):
        return self.name

    def get_subsections(self):
        return self.subsections

    def get_tracks(self):
        return self.tracks

    def on_selected(self, parent):
        try:
            if not parent.is_open:
                parent.is_open = True
                for subsection in self.subsections:
                    subsection_label = MusicListLabel(SubSectionLabel(subsection, text=subsection.get_name()))
                    parent.add_widget(subsection_label)
                for track in self.tracks:
                    track_label = MusicListLabel(TrackLabel(track, text=track.name))
                    parent.add_widget(track_label)
            else:
                parent.is_open = False
                parent.hide_tracks()
        except AttributeError:
            pass


class TrackSubSection:

    def __init__(self, name):
        self.name = name
        self.tracks = []

    def add_track(self, track_name):
        self.tracks.append(track_name)

    def add_subsubsection(self, subsubsection):
        self.tracks.append(subsubsection)

    def get_name(self):
        return self.name

    def get_tracks(self):
        return self.tracks

    def on_selected(self, parent):
        try:
            if not parent.is_open:
                parent.is_open = True
                for track in self.tracks:
                    if self.track_is_subsection(track):
                        parent.add_widget(track)
                    else:
                        track_label = MusicListLabel(TrackLabel(track, text=track.name))
                        parent.add_widget(track_label)
            else:
                parent.is_open = False
                parent.hide_tracks()
        except AttributeError:
            pass

    def track_is_subsection(self, track):
        try:
            temp = track.url
            return False
        except AttributeError:
            return True


class Track:

    def __init__(self, name, url, section, subsection):
        self.name = name
        self.url = url
        self.section = section
        self.subsection = subsection

    def on_selected(self):
        main_scr = App.get_running_app().get_main_screen()
        main_scr.ooc_window.music_tab.on_music_play(url=self.url, track_name=self.name)


class MusicListLabel(BoxLayout):

    def __init__(self, display, **kwargs):
        super(MusicListLabel, self).__init__(**kwargs)
        self.element_display = display
        self.add_widget(self.element_display)
        self.is_open = False

    def hide_tracks(self):
        self.clear_widgets()
        self.add_widget(self.element_display)


class MusicListView(ScrollView):

    music_box_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MusicListView, self).__init__(**kwargs)

    def add_element(self, el):
        self.music_box_layout.add_widget(el)


class SearchResults(ScrollView):

    def __init__(self, **kwargs):
        super(SearchResults, self).__init__(**kwargs)
        self.scroll_type = ['bars']
        self.bar_width = 10

    def add_label(self, label):
        self.children[0].add_widget(label)

    def clear_labels(self):
        self.children[0].clear_widgets()


class MusicList(TabbedPanelItem):
    music_list_view = ObjectProperty(None)
    search_bar = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MusicList, self).__init__(**kwargs)
        self.tracks = {}
        self.search_space = []
        self.track_search_space = []
        self.section_search_space = []
        self.subsection_search_space = []
        self.sections = {}
        self.subsections = {}
        self.search_results = SearchResults()
        self.search_done = False
        self.current_section = None
        self.current_subsection = None

    def ready(self):
        self.load_tracks()

    def load_tracks(self):
        try:
            with open('musiclist.txt', mode='r', encoding='utf-16') as f:
                for line in f:
                    if len(line) > 2:
                        self.build_from_line(line)
        except FileNotFoundError:
            Logger.warning('Music: musiclist.txt not found')
            return
        self.track_search_space = list(self.tracks.keys())
        self.section_search_space = list(self.sections.keys())
        self.subsection_search_space = list(self.subsections.keys())
        self.track_search_space.sort(key=str.lower)
        self.section_search_space.sort(key=str.lower)
        self.subsection_search_space.sort(key=str.lower)

    def build_from_line(self, line):
        music_list_element = None
        if line.startswith('['):
            section = line[1:-2]
            track_section = TrackSection(section)
            self.sections[section.lower()] = track_section
            self.current_section = track_section
            self.current_subsection = None
            music_list_element = MusicListLabel(SectionLabel(track_section, text=section))
        elif line.startswith('<'):
            subsection = line[1:-2]
            track_subsection = TrackSubSection(subsection)
            self.subsections[subsection.lower()] = track_subsection
            self.current_subsection = track_subsection
            self.current_section.add_subsection(track_subsection)
        elif line.startswith('\\'):
            subsubsection = line[1:-2]
            self.current_subsection.add_subsubsection(MusicListLabel(SubSubSectionLabel(text=subsubsection)))
        else:
            track_name, track_url = line.split(':', 1)
            track_url = track_url.strip()
            track = Track(track_name, track_url, self.current_section, self.current_subsection)
            self.tracks[track_name.lower()] = track
            if self.current_subsection is None:
                self.current_section.add_track(track)
            else:
                self.current_subsection.add_track(track)
        if music_list_element is not None:
            self.music_list_view.add_element(music_list_element)

    def search(self, target):
        if target == "":
            self.clear_search()
            return
        if self.search_done:
            self.clear_search()
        self.search_bar.text = ""
        Clock.schedule_once(self.refocus)
        is_section = False
        is_subsection = False
        if target.startswith('['):
            target = target.strip('[]')
            is_section = True
            self.search_space = self.section_search_space
        elif target.startswith('<'):
            target = target.strip('<>')
            is_subsection = True
            self.search_space = self.subsection_search_space
        else:
            self.search_space = self.track_search_space
        result = self.find_track(target)
        if result is None:
            return
        added_sections = []
        added_subsections = []
        for track in result:
            if is_section and track in self.sections:
                section = self.sections[track]
                self.add_section_to_search_result(section)
                for section_track in section.get_tracks():
                    self.add_track_to_search_result(section_track)
                for subsection in section.get_subsections():
                    self.add_subsection_to_search_result(subsection)
                    for track_object in subsection.get_tracks():
                        self.add_track_to_search_result(track_object)
            elif is_subsection and track in self.subsections:
                subsection = self.subsections[track]
                self.add_subsection_to_search_result(subsection)
                for track_object in subsection.get_tracks():
                    self.add_track_to_search_result(track_object)
            elif not is_subsection and not is_section:
                track_section = self.tracks[track.lower()].section
                if track_section not in added_sections:
                    self.add_section_to_search_result(track_section)
                    added_sections.append(track_section)
                track_subsection = self.tracks[track.lower()].subsection
                if track_subsection is not None:
                    if track_subsection not in added_subsections:
                        self.add_subsection_to_search_result(track_subsection)
                        added_subsections.append(track_subsection)
                self.add_track_to_search_result(self.tracks[track])
        layout = self.content
        layout.remove_widget(self.music_list_view)
        layout.add_widget(self.search_results, index=1)

    def add_subsection_to_search_result(self, subsection):
        subsection_label = SubSectionLabel(subsection)
        subsection_label.text = subsection.get_name()
        self.search_results.add_label(subsection_label)

    def add_section_to_search_result(self, section):
        section_label = SectionLabel(section)
        section_label.text = section.get_name()
        self.search_results.add_label(section_label)

    def add_track_to_search_result(self, track):
        try:
            track_label = TrackLabel(track, text=track.name)
            self.search_results.add_label(track_label)
        except AttributeError:
            pass

    def find_track(self, target):
        found_index = binary_search(self.search_space, target)
        if found_index is None:
            return None
        self.search_done = True
        i = found_index
        current_track = self.search_space[i].lower()
        result = []
        while current_track.startswith(target.lower()):
            result.append(current_track)
            if i == len(self.search_space) - 1:
                break
            i += 1
            current_track = self.search_space[i].lower()
        i = found_index
        if i > 0:
            i -= 1
            current_track = self.search_space[i].lower()
            while current_track.startswith(target.lower()):
                result.append(current_track)
                if i == 0:
                    break
                i -= 1
                current_track = self.search_space[i].lower()
        return result

    def refocus(self, *args):
        self.search_bar.focus = True

    def clear_search(self):
        if not self.search_done:
            return
        self.search_done = False
        self.search_results.clear_labels()
        layout = self.content
        layout.remove_widget(self.search_results)
        layout.add_widget(self.music_list_view, index=1)


class LeftTab(TabbedPanel):
    sprite_preview = ObjectProperty(None)
    sprite_settings = ObjectProperty(None)
    trans_slider = ObjectProperty(None)
    speed_slider = ObjectProperty(None)
    music_list = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LeftTab, self).__init__(**kwargs)

    def ready(self, main_scr):
        main_scr.sprite_preview = self.sprite_preview
        main_scr.sprite_settings = self.sprite_settings
        config = App.get_running_app().config
        self.trans_slider.value = config.getdefaultint('other', 'textbox_transparency', 60)
        self.speed_slider.value = config.getdefaultint('other', 'textbox_speed', 60)
        self.music_list.ready()

    def on_trans_slider_value(self, *args):
        config = App.get_running_app().config
        value = int(self.trans_slider.value)
        config.set('other', 'textbox_transparency', value)

    def on_speed_slider_value(self, *args):
        config = App.get_running_app().config
        value = int(self.speed_slider.value)
        config.set('other', 'textbox_speed', value)

    def on_dance_checkbox(self, active):
        app: MysteryOnline.main.MysteryOnlineApp = App.get_running_app()
        user: MysteryOnline.user.User = app.get_user()
        user.set_dance(active)
        app.send_current_nullpost()

