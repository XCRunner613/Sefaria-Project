# -*- coding: utf-8 -*-

from .framework import AtomicTest, TestSuite, one_of_these_texts_present_in_element
from sefaria.utils.hebrew import has_cantillation
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support.expected_conditions import title_contains, staleness_of, element_to_be_clickable, visibility_of_element_located, invisibility_of_element_located, text_to_be_present_in_element

from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation, strip_nikkud
from selenium.common.exceptions import WebDriverException

import time  # import stand library below name collision in sefaria.model
import urllib.parse

TEMPER = 30


class ReaderSuite(TestSuite):
    """
    Suite of reader tests that are run one after the other, without page reload
    """
    every_build = True

    def setup(self):
        # try:
        #    self.driver.set_window_size(900, 1100)
        #except WebDriverException:
        #    pass
        self.load_toc(my_temper=60)
        #self.driver.delete_all_cookies()
        self.click_accept_cookies()
        #self.set_cookies_cookie()
        
    def teardown(self):
        self.driver.close()


class PageloadSuite(TestSuite):
    """
    Tests that load pages and don't make any assumptions about starting or ending state
    """
    every_build = True

    def setup(self):
        # try:
        #    self.driver.set_window_size(900, 1100)
        #except WebDriverException:
        #    pass
        self.load_toc(my_temper=60)
        #self.driver.delete_all_cookies()
        self.click_accept_cookies()
        #self.set_cookies_cookie()
        
    def teardown(self):
        self.driver.close()


class DeepReaderSuite(TestSuite):
    #TODO: When do we run this?
    every_build = False


class EditorSuite(TestSuite):
    """
    Tests that do editor things
    """
    every_build = False
    temp_sheet_id = None

    def setup(self):
        from urllib.parse import urlparse
        self.load_toc(my_temper=60)
        self.login_user()
        self.enable_new_editor()
        self.click_accept_cookies()
        self.new_sheet_in_editor()
        self.nav_to_end_of_editor()
        self.temp_sheet_id = urlparse(self.get_current_url()).path.rsplit("/", 1)[-1]

    def teardown(self):
        self.driver.get(f'{self.base_url}/api/sheets/{self.temp_sheet_id}/delete')
        self.disable_new_editor()
        self.driver.close()


class DeleteContentInEditor(AtomicTest):
    suite_class = EditorSuite
    every_build = False
    single_panel = False  # No source sheets on mobile
    def body(self):
        self.delete_sheet_content("back")
        self.delete_sheet_content("forward")
        self.catch_js_error()


class AddSourceToEditor(AtomicTest):
    suite_class = EditorSuite
    every_build = False
    single_panel = False  # No source sheets on mobile

    def body(self):
        self.add_source("Psalms 43:4")
        sheet_items = self.driver.find_elements_by_css_selector(".sheetItem")
        # sheet_items_and_spacers = self.driver.find_elements_by_css_selector(".editorContent div")
        sheet_items_and_spacers = self.driver.find_elements_by_css_selector(".editorContent>div")


        print(len(sheet_items))

        last_sheet_item = sheet_items[-1]
        added_source = last_sheet_item.find_element_by_css_selector(".SheetSource") # will throw error if doesn't exist

        print(last_sheet_item == sheet_items_and_spacers[-2])

        # print(last_sheet_item.get_attribute('innerHTML'))

        spacer_after_source = last_sheet_item.find_elements_by_css_selector(".sheetItem")

        print(len(spacer_after_source))

        # assert len(sheet_items) == 1


class AddSheetContent(AtomicTest):
    suite_class = EditorSuite
    every_build = False
    single_panel = False  # No source sheets on mobile

    def body(self):
        self.type_lorem_ipsum_text("he")
        self.type_lorem_ipsum_text("en")
        self.catch_js_error()
        assert 1 == 1
        # edited_sheet = self.get_sheet_html()
        # sheetURL = self.get_current_url()
        # self.driver.get(sheetURL)
        # loaded_sheet = self.get_sheet_html()
        # assert edited_sheet == loaded_sheet


class SinglePanelOnMobile(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    multi_panel = False

    def body(self):
        self.nav_to_text_toc(["Tanakh"], "Joshua")
        self.click_text_toc_section("Joshua 1")
        elems = self.driver.find_elements_by_css_selector(".readerApp.multiPanel")
        assert len(elems) == 0
        self.click_segment("Joshua 1:1")
        elems = self.driver.find_elements_by_css_selector(".readerApp .readerPanelBox")
        assert len(elems) == 1

        self.click_segment_to_close_commentary("Joshua 1:1")  # Close commentary window on mobile


class PagesLoad(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_toc()
        self.click_toc_category("Midrash").click_toc_text("Ein Yaakov")
        self.load_ref("Psalms.104")
        print("Done loading Psalms 104")
        self.load_ref("Job.3")
        print("Done loading Job 3")
        self.load_topics()
        print("Done loading topics")
        self.load_gardens()
        print("Done loading gardens")
        self.load_home()
        print("Done loading home")
        self.load_people()
        print("Done loading people ")

class PagesLoadLoggedIn(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_toc()
        self.login_user()
        self.load_my_profile()
        # self.load_notifications()
        print("Done loading user")
        # self.load_notifications()
        self.nav_to_account() # load_account might be superceded by load_my_profile or nav_to_account
        print("Done loading account")
        self.load_private_sheets()
        print("Done loading private sheets")
        ## self.load_private_groups() # fails -- /my/groups no longer exists
        print("Done loading private groups")
        self.load_notifications()


class InTextSectionHeaders(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_toc()
        self.click_toc_category("Midrash")
        self.click_toc_text("Ein Yaakov")
        self.click_source_title()
        self.click_masechet_and_chapter('2','3')
        section = self.get_section_txt('1')
        assert 'רבי זירא הוה משתמיט' in strip_nikkud(section)

        self.load_toc()
        self.click_toc_category("Midrash").click_toc_text("Seder Olam Rabbah")
        self.click_source_title()
        self.click_chapter('4')
        section = self.get_section_txt('1')
        assert 'פרק ד ' == section


class ChangeTextLanguage(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_ref("Genesis 1")
        expected_heb = 'בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃'
        expected_eng_closed = 'When God began to create heaven and earth—'
        expected_eng_open = 'In the beginning God created the heaven and the earth.'
        sgmnt_eng = self.get_nth_section_english(1)
        sgmnt_heb = self.get_nth_section_hebrew(1)
        str_eng = sgmnt_eng.text.strip()
        str_heb = sgmnt_heb.text.strip()
        # not sure why, but he strings aren't equal unless vowels are stripped
        expected_heb_stripped = strip_cantillation(expected_heb, strip_vowels=True)
        str_heb_stripped = strip_cantillation(str_heb, strip_vowels=True)
        assert expected_heb_stripped == str_heb_stripped, "'{}' does not equal '{}'".format(expected_heb_stripped, str_heb_stripped)
        assert str_eng in [expected_eng_open, expected_eng_closed], "'{}' does not equal '{}' or '{}'".format(str_eng, expected_eng_closed, expected_eng_open)
        self.toggle_on_text_settings()
        self.toggle_language_hebrew()
        assert 'hebrew' in self.get_content_language()
        assert 'english' not in self.get_content_language()
        assert 'bilingual' not in self.get_content_language()
        assert sgmnt_heb.is_displayed() == True
        assert sgmnt_eng.is_displayed() == False
        self.toggle_on_text_settings()
        self.toggle_language_english()
        assert 'hebrew' not in self.get_content_language()
        assert 'english' in self.get_content_language()
        assert 'bilingual' not in self.get_content_language()
        assert sgmnt_heb.is_displayed() == False
        assert sgmnt_eng.is_displayed() == True
        self.toggle_on_text_settings()
        self.toggle_language_bilingual()
        assert 'hebrew' not in self.get_content_language()
        assert 'english' not in self.get_content_language()
        assert 'bilingual' in self.get_content_language()
        assert sgmnt_heb.is_displayed() == True
        assert sgmnt_eng.is_displayed() == True
        self.get_content_language()


class TextSettings(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        larger = 21.6
        smaller = 18.7826
        just_text = 'בראשית ברא אלהים את השמים ואת הארץ'
        text_with_vowels = 'בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ׃'
        text_with_cantillation = 'בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃'
        self.load_ref("Genesis 1")
        # 1] Language: heb/eng/bilingual
        self.toggle_on_text_settings()
        self.toggle_language_english()
        assert not self.get_nth_section_hebrew(1).is_displayed()
        assert self.get_nth_section_english(1).is_displayed()

        self.toggle_on_text_settings()
        self.toggle_language_hebrew()
        assert self.get_nth_section_hebrew(1).is_displayed()
        assert not self.get_nth_section_english(1).is_displayed()

        self.toggle_on_text_settings()
        self.toggle_language_bilingual()
        assert self.get_nth_section_hebrew(1).is_displayed()
        assert self.get_nth_section_english(1).is_displayed()

        # 2] Layout: left/right/stacked
        if not self.single_panel:
            self.toggle_on_text_settings()
            self.toggle_bilingual_layout_heLeft()
            assert self.get_content_layout_direction() == 'left'

            self.toggle_on_text_settings()
            self.toggle_bilingual_layout_heRight()
            assert self.get_content_layout_direction() == 'right'

            self.toggle_on_text_settings()
            self.toggle_bilingual_layout_stacked()
            assert self.get_content_layout_direction() == 'stacked'

        # 3] Font size: small/large
        self.toggle_on_text_settings()
        font_size_original = self.get_font_size()
        self.toggle_fontSize_smaller()
        font_size_smaller = self.get_font_size()

        # self.toggle_text_settings()
        self.toggle_fontSize_larger()
        font_size_larger = self.get_font_size()
        assert font_size_larger > font_size_smaller

        # 4] Aliyot: on off
        # todo: Set up scroll_to_segment then enable this
        # self.toggle_aliyotTorah_aliyotOn()
        # self.scroll_to_segment(Ref("Genesis 2:4"))
        # assert self.is_aliyot_displayed()

        # self.toggle_on_text_settings()
        # self.toggle_aliyotTorah_aliyotOff()
        # self.scroll_reader_panel_to_bottom()
        # assert not self.is_aliyot_displayed()

        # 5] Vocalization: vowels and cantillation
        # self.toggle_on_text_settings()
        self.toggle_vowels_partial()
        assert self.get_nth_section_hebrew(1).text.strip() == text_with_vowels, "'{}' does not equal '{}'".format(self.get_nth_section_hebrew(1).text.strip(), text_with_vowels)

        self.toggle_on_text_settings()
        self.toggle_vowels_all()
        assert self.get_nth_section_hebrew(1).text.strip() == text_with_cantillation, "'{}' does not equal '{}'".format(self.get_nth_section_hebrew(1).text.strip(), text_with_cantillation)

        self.toggle_on_text_settings()
        self.toggle_vowels_none()
        assert self.get_nth_section_hebrew(1).text.strip() == just_text, "'{}' does not equal '{}'".format(self.get_nth_section_hebrew(1).text.strip(), just_text)

'''
class TanakhCantillationAndVowels(AtomicTest):
    suite_class = ReaderSuite
    every_build = False

    def body(self):
        self.load_home()
        self.click_get_started()
        # self.toggle_on_text_settings()
        # self.toggle_vowels_partial()
        # assert not has_cantillation(self.get_nth_section_hebrew(1).text, False)
        # assert has_cantillation(self.get_nth_section_hebrew(1).text, True)
        #
        # self.toggle_on_text_settings()
        # self.toggle_vowels_all()
        # assert has_cantillation(self.get_nth_section_hebrew(1).text, False)
        # assert has_cantillation(self.get_nth_section_hebrew(1).text, True)
        #
        # self.toggle_on_text_settings()
        # self.toggle_vowels_none()
        # assert not has_cantillation(self.get_nth_section_hebrew(1).text)
        # assert not has_cantillation(self.get_nth_section_hebrew(1).text, False)
        # # Make sure switching to a differernt book doesn't change the cantillation/vowels settings
        # self.nav_to_text_toc(["Tanakh"], "Joshua")
        # self.load_ref("Joshua 1")
        # assert not has_cantillation(self.get_nth_section_hebrew(1).text)
        # assert not has_cantillation(self.get_nth_section_hebrew(1).text, False)
'''

class AliyotAndCantillationToggles(AtomicTest):
    suite_class = ReaderSuite
    every_build = False

    def body(self):
        self.browse_to_ref("Darashos HaRan 1")        
        assert not has_cantillation(self.get_nth_section_hebrew(1).text)
        assert not has_cantillation(self.get_nth_section_hebrew(1).text, False)
        self.toggle_on_text_settings()
        assert not self.is_aliyot_toggleSet_displayed()
        assert not self.is_vocalization_toggleSet_displayed()

        self.browse_to_ref("Berakhot 2b")
        self.toggle_on_text_settings()
        assert not self.is_aliyot_toggleSet_displayed()
        assert self.is_vocalization_toggleSet_displayed()
        
        self.browse_to_ref("Joshua 2")
        self.toggle_on_text_settings()
        assert not self.is_aliyot_toggleSet_displayed()
        assert self.is_vocalization_toggleSet_displayed()
        
        self.browse_to_ref("Genesis 1")
        self.toggle_on_text_settings()
        assert self.is_aliyot_toggleSet_displayed()
        assert self.is_vocalization_toggleSet_displayed()


class SideBarEntries(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    single_panel = False
    # todo: make this work on mobile.
    # "sidebar" elements will need to be scrolled into view before clicking

    def body(self):
        self.login_user()
        self.browse_to_ref("Ecclesiastes 1")
        self.click_segment("Ecclesiastes 1:1")

        sections = ("Commentary", "Targum", "Talmud", "Midrash", "Midrash")
        for section in sections:
            self.click_sidebar_entry(section)
            self.click_resources_on_sidebar()

        self.click_sidebar_button("Other Text")
        assert self.is_sidebar_browse_title_displayed()
        assert self.is_sidebar_calendar_title_displayed()
        self.driver.find_element_by_css_selector('.readerNavMenuMenuButton').click()

        self.click_sidebar_button("Sheets")
        self.click_resources_on_sidebar()

        self.click_sidebar_button("Notes")
        self.click_resources_on_sidebar()

        self.click_sidebar_button("About")
        msg = self.driver.find_element_by_css_selector('#panel-1 > div.readerContent > div > div > div > section > div.detailsSection > h2 > span.int-en').get_attribute('innerHTML')
        assert msg == 'About This Text'
        self.click_resources_on_sidebar()

        self.click_sidebar_button("Translations")
        #todo: This version doesn't show up on title bar.  Rework this to change to a version that will show on bar.
        #url1 = self.get_current_url()
        #title1 = self.get_current_content_title()
        assert self.get_sidebar_nth_version_button(1).text in ['Current Translation', 'מהדורה נוכחית'],  "'{}' does not equal 'Current Translation'".format(self.get_sidebar_nth_version_button(1).text)
        assert self.get_sidebar_nth_version_button(2).text in ['Select Translation', 'בחירת תרגום'],  "'{}' does not equal 'Select Translation'".format(self.get_sidebar_nth_version_button(2).text)
        self.click_sidebar_nth_version_button(2)
        #url2 = self.get_current_url()
        #title2 = self.get_current_content_title()
        #assert url1 != url2, u"'{}' equals '{}'".format(url1, url2)
        #assert title1 != title2,  u"'{}' equals '{}'".format(title1, title2)
        time.sleep(1)
        assert self.get_sidebar_nth_version_button(1).text in ['Select Translation', 'בחירת תרגום'],  u"'{}' does not equal 'Select Translation'".format(self.get_sidebar_nth_version_button(1).text)
        assert self.get_sidebar_nth_version_button(2).text in ['Current Translation', 'מהדורה נוכחית'], u"'{}' does not equal 'Current Translation'".format(self.get_sidebar_nth_version_button(2).text)
        self.click_resources_on_sidebar()

        self.click_sidebar_button("Web Pages")
        self.click_resources_on_sidebar()

        self.click_sidebar_button("Tools")
        self.click_sidebar_button("Share")
        '''
        Buggy.  Doesn't work on Safari. Mobile?
        self.click_sidebar_facebook_link()
        url1 = self.get_newly_opened_tab_url()
        assert 'facebook.com' in url1, u"'{}' not in '{}'".format('facebook.com', url1)
        self.close_tab_and_return_to_prev_tab()
        self.click_resources_on_sidebar()
        self.click_tools_on_sidebar()
        self.click_share_on_sidebar()
        self.click_sidebar_twitter_link()
        url1 = self.get_newly_opened_tab_url()
        assert 'twitter.com' in url1, u"'{}' not in '{}'".format('twitter.com', url1)
        self.close_tab_and_return_to_prev_tab()
        '''
        self.click_resources_on_sidebar()
        # self.click_tools_on_sidebar()     #NOT checking the email option, not to open an email client. Leaving here thoupgh, just in case.
        # self.click_share_on_sidebar()
        # self.click_email_twitter_link()
        # self.click_resources_on_sidebar()
        # self.click_tools_on_sidebar()
        # self.click_add_translation_on_sidebar()   # Time out. Is this a bug?
        # self.back()

        self.click_sidebar_button("Tools")
        self.click_sidebar_button("Add Connection")
        time.sleep(1)
        assert self.is_sidebar_browse_title_displayed()
        assert self.is_sidebar_calendar_title_displayed()


class ChangeSiteLanguage(AtomicTest):
    # Switch between Hebrew and English and sample a few of the objects to make sure 
    # the language has actually changed.
    suite_class = ReaderSuite
    every_build = False

    def body(self):
        self.nav_to_toc()
        self.click_ivrit_link()
        if 'safari' in self.driver.name or "Safari" in self.driver.name:
            time.sleep(1)
        assert self.driver.find_element_by_class_name('interface-hebrew') != None
        
        self.click_english_link()
        if 'safari' in self.driver.name or "Safari" in self.driver.name:
            time.sleep(1)
        assert self.driver.find_element_by_class_name('interface-english') != None


class LinkExplorer(AtomicTest):
    # Make sure all Tanach books and Mashechtot are displayed, and sample some entries to check 
    # that torah>nevi'im>ketuvim and the Sedarim are in the correct order
    suite_class = PageloadSuite
    every_build = False
    def body(self):
        self.driver.get(urllib.parse.urljoin(self.base_url,"/explore"))
        #todo ^ add a wait there that is connected to content

        if 'safari' in self.driver.name or "Safari" in self.driver.name:
            time.sleep(1)  # Might fail on Safari without this sleep

        assert self.get_object_by_id('Genesis').is_displayed()
        assert self.get_object_by_id('Exodus').is_displayed()
        assert self.get_object_by_id('Leviticus').is_displayed()
        assert self.get_object_by_id('Numbers').is_displayed()
        assert self.get_object_by_id('Deuteronomy').is_displayed()
        assert float(self.get_object_by_id('Deuteronomy').get_attribute('cx')) < float(self.get_object_by_id('Joshua').get_attribute('cx'))
        assert self.get_object_by_id('Joshua').is_displayed()
        assert self.get_object_by_id('Judges').is_displayed()
        assert self.get_object_by_id('I-Samuel').is_displayed()
        assert self.get_object_by_id('II-Samuel').is_displayed()
        assert self.get_object_by_id('I-Kings').is_displayed()
        assert self.get_object_by_id('II-Kings').is_displayed()
        assert self.get_object_by_id('Isaiah').is_displayed()
        assert self.get_object_by_id('Jeremiah').is_displayed()
        assert self.get_object_by_id('Ezekiel').is_displayed()
        assert self.get_object_by_id('Hosea').is_displayed()
        assert self.get_object_by_id('Joel').is_displayed()
        assert self.get_object_by_id('Amos').is_displayed()
        assert self.get_object_by_id('Obadiah').is_displayed()
        assert self.get_object_by_id('Jonah').is_displayed()
        assert self.get_object_by_id('Micah').is_displayed()
        assert self.get_object_by_id('Nahum').is_displayed()
        assert self.get_object_by_id('Habakkuk').is_displayed()
        assert self.get_object_by_id('Zephaniah').is_displayed()
        assert self.get_object_by_id('Haggai').is_displayed()
        assert self.get_object_by_id('Zechariah').is_displayed()
        assert self.get_object_by_id('Malachi').is_displayed()
        assert float(self.get_object_by_id('Malachi').get_attribute('cx')) < float(self.get_object_by_id('Psalms').get_attribute('cx'))
        assert self.get_object_by_id('Psalms').is_displayed()
        assert self.get_object_by_id('Proverbs').is_displayed()
        assert self.get_object_by_id('Job').is_displayed()
        assert self.get_object_by_id('Song-of-Songs').is_displayed()
        assert self.get_object_by_id('Ruth').is_displayed()
        assert self.get_object_by_id('Lamentations').is_displayed()
        assert self.get_object_by_id('Ecclesiastes').is_displayed()
        assert self.get_object_by_id('Esther').is_displayed()
        assert self.get_object_by_id('Daniel').is_displayed()
        assert self.get_object_by_id('Ezra').is_displayed()
        assert self.get_object_by_id('Nehemiah').is_displayed()
        assert self.get_object_by_id('I-Chronicles').is_displayed()
        assert self.get_object_by_id('II-Chronicles').is_displayed()
        assert self.get_object_by_id('Berakhot').is_displayed()
        assert float(self.get_object_by_id('Berakhot').get_attribute('cx')) < float(self.get_object_by_id('Shabbat').get_attribute('cx'))
        assert self.get_object_by_id('Shabbat').is_displayed()
        assert self.get_object_by_id('Eruvin').is_displayed()
        assert self.get_object_by_id('Pesachim').is_displayed()
        assert self.get_object_by_id('Rosh-Hashanah').is_displayed()
        assert self.get_object_by_id('Yoma').is_displayed()
        assert self.get_object_by_id('Sukkah').is_displayed()
        assert self.get_object_by_id('Beitzah').is_displayed()
        assert self.get_object_by_id('Taanit').is_displayed()
        assert self.get_object_by_id('Megillah').is_displayed()
        assert self.get_object_by_id('Moed-Katan').is_displayed()
        assert self.get_object_by_id('Chagigah').is_displayed()
        assert float(self.get_object_by_id('Chagigah').get_attribute('cx')) < float(self.get_object_by_id('Yevamot').get_attribute('cx'))
        assert self.get_object_by_id('Yevamot').is_displayed()
        assert self.get_object_by_id('Ketubot').is_displayed()
        assert self.get_object_by_id('Nedarim').is_displayed()
        assert self.get_object_by_id('Nazir').is_displayed()
        assert self.get_object_by_id('Sotah').is_displayed()
        assert self.get_object_by_id('Gittin').is_displayed()
        assert self.get_object_by_id('Kiddushin').is_displayed()
        assert float(self.get_object_by_id('Kiddushin').get_attribute('cx')) < float(self.get_object_by_id('Bava-Kamma').get_attribute('cx'))
        assert self.get_object_by_id('Bava-Kamma').is_displayed()
        assert self.get_object_by_id('Bava-Metzia').is_displayed()
        assert self.get_object_by_id('Bava-Batra').is_displayed()
        assert self.get_object_by_id('Sanhedrin').is_displayed()
        assert self.get_object_by_id('Makkot').is_displayed()
        assert self.get_object_by_id('Shevuot').is_displayed()
        assert self.get_object_by_id('Avodah-Zarah').is_displayed()
        assert self.get_object_by_id('Horayot').is_displayed()
        assert float(self.get_object_by_id('Kiddushin').get_attribute('cx')) < float(self.get_object_by_id('Horayot').get_attribute('cx'))
        assert self.get_object_by_id('Zevachim').is_displayed()
        assert self.get_object_by_id('Menachot').is_displayed()
        assert self.get_object_by_id('Chullin').is_displayed()
        assert self.get_object_by_id('Bekhorot').is_displayed()
        assert self.get_object_by_id('Arakhin').is_displayed()
        assert self.get_object_by_id('Temurah').is_displayed()
        assert self.get_object_by_id('Keritot').is_displayed()
        assert self.get_object_by_id('Meilah').is_displayed()
        assert self.get_object_by_id('Tamid').is_displayed()
        assert float(self.get_object_by_id('Tamid').get_attribute('cx')) < float(self.get_object_by_id('Niddah').get_attribute('cx'))
        assert self.get_object_by_id('Niddah').is_displayed()


class ReadingHistory(AtomicTest):
    suite_class = PageloadSuite
    single_panel = False
    every_build = True

    def body(self):
        # Using a short chapter can cause the text to fail if the following section is
        # counted as a view and saved in recent in place of the named chapter.
        self.load_toc()
        self.search_ref("Joshua 1")
        self.nav_to_history().click_toc_recent("Joshua 1")
        self.browse_to_ref("Berakhot 23b")
        time.sleep(3)
        self.nav_to_history().click_toc_recent("Berakhot 23b")

        # Ensure History sticks on reload
        self.load_toc().nav_to_history().click_toc_recent("Joshua 1")


class NavToRefAndClickSegment(AtomicTest):
    suite_class = ReaderSuite
    every_build = True

    def body(self):
        self.browse_to_ref("Job 3:4").click_segment("Job 3:4")
        assert "Job.3.4" in self.driver.current_url, self.driver.current_url
        assert "with=all" in self.driver.current_url, self.driver.current_url

        # If we're one level deep in a menu, go back.
        elems = self.driver.find_elements_by_css_selector(".connectionsHeaderTitle.active")
        if len(elems) > 0:
            elems[0].click()

        self.click_category_filter("Commentary")
        self.click_text_filter("Ibn Ezra")

        assert "Job.3.4" in self.driver.current_url, self.driver.current_url
        assert "with=Ibn%20Ezra" in self.driver.current_url or "with=Ibn Ezra" in self.driver.current_url, self.driver.current_url

        self.click_segment_to_close_commentary("Job 3:4")  #  This is needed on mobile, to close the commentary window


class LoadRefAndClickSegment(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_ref("Job 3:4").click_segment("Job 3:4")
        assert "Job.3.4" in self.driver.current_url, self.driver.current_url
        assert "with=all" in self.driver.current_url, self.driver.current_url

        self.click_category_filter("Commentary")
        self.click_text_filter("Ibn Ezra")

        assert "Job.3.4" in self.driver.current_url, self.driver.current_url
        assert "with=Ibn%20Ezra" in self.driver.current_url or "with=Ibn Ezra" in self.driver.current_url, self.driver.current_url


class LoadRefWithCommentaryAndClickOnCommentator(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_ref("Job 3:4", filter="all").click_category_filter("Commentary").click_text_filter("Rashi")
        assert "Job.3.4" in self.driver.current_url, self.driver.current_url
        assert "with=Rashi" in self.driver.current_url, self.driver.current_url


class NavAndVerifyTextTOC(AtomicTest):
    suite_class = ReaderSuite
    every_build = True

    def body(self):
        navs = [
            (["Tanakh"], "Genesis"),  # Simple Text
            (["Talmud"], "Shabbat"),  # Talmud Numbering
            (["Tanakh", "Ibn Ezra"], "Ibn Ezra on Psalms"),  # Commentary on Simple text
            (["Kabbalah"], "Zohar"),  # Zohar, just cuz
            (["Talmud", "Tosafot"], "Tosafot on Shabbat"),  # Commentary on Talmud
            (["Liturgy"], "Pesach Haggadah") # Complex text
        ]

        for (cats, text_title) in navs:
            self.nav_to_text_toc(cats, text_title)


class LoadAndVerifyIndepenedentTOC(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        titles = [
            "Genesis",  # Simple Text
            "Shabbat",  # Talmud Numbering
            "Ibn Ezra on Psalms",  # Commentary on Simple text
            "Zohar",  # Zohar, just cuz
            "Tosafot on Shabbat",  # Commentary on Talmud
            "Pesach Haggadah" # Complex text
        ]
        for title in titles:
            self.load_text_toc(title)


class LoadSpanningRefAndOpenConnections(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_ref("Shabbat 2a-2b")
        self.click_segment("Shabbat 2a:1")


class NavToSpanningRefAndOpenConnections(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    single_panel = False

    def body(self):
        self.search_ref("Shabbat 2a-2b")
        self.click_segment("Shabbat 2a:1")


class PermanenceOfRangedRefs(AtomicTest):
    """
    There have been bugs around Links with ranged references.
    This test checks that they are present, and that they survive to a second click (they had previously been ephemeral.)
    """
    suite_class = ReaderSuite
    every_build = True
    single_panel = False  # Segment clicks on mobile have different semantics  todo: write this for mobile?  It's primarily a data test.

    def body(self):
        self.search_ref("Shabbat 2a")
        self.click_segment("Shabbat 2a:1")
        self.click_category_filter("Mishnah")
        assert self.find_text_filter("Mishnah Shabbat")
        self.click_segment("Shabbat 2a:2")
        assert self.find_text_filter("Mishnah Shabbat")
        self.click_segment("Shabbat 2a:1")
        assert self.find_text_filter("Mishnah Shabbat")
        self.click_segment("Shabbat 2a:2")
        assert self.find_text_filter("Mishnah Shabbat")


class NavToTocAndCheckPresenceOfDownloadButton(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    exclude = ['And/5.1', 'iPh5s']  # Android driver doesn't support "Select" class. Haven't found workaround.

    # iPhone has an unrelated bug where a screen size refresh mid-test causes this to fail.
    def body(self):
        # Load Shabbat TOC and scroll to bottom
        self.nav_to_text_toc(["Talmud"], "Shabbat").scroll_nav_panel_to_bottom()

        # Check that DL Button is visible and not clickable
        visible = self.driver.execute_script(
            'var butt = document.getElementsByClassName("downloadButtonInner")[0]; ' + \
            'var butt_bot = butt.getBoundingClientRect().top + butt.getBoundingClientRect().height; ' + \
            'var win_height = window.innerHeight; ' + \
            'return win_height > butt_bot;'
        )
        assert visible, "Download button below page"
        # This isn't sufficient - it only checks if it's visible in the DOM
        # WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".downloadButtonInner")))

        WebDriverWait(self.driver, TEMPER).until(
            invisibility_of_element_located((By.CSS_SELECTOR, '.dlVersionFormatSelect + a')))

        # Select version and format
        select1 = Select(self.driver.find_element_by_css_selector('.dlVersionTitleSelect'))
        select1.select_by_value("Wikisource Talmud Bavli/he")
        select2 = Select(self.driver.find_element_by_css_selector('.dlVersionFormatSelect'))
        select2.select_by_value("csv")

        # Check that DL button is clickable
        WebDriverWait(self.driver, TEMPER).until(
            visibility_of_element_located((By.CSS_SELECTOR, '.dlVersionFormatSelect + a')))


class LoadTocAndCheckPresenceOfDownloadButton(AtomicTest):
    suite_class = PageloadSuite
    every_build = True
    exclude = ['And/5.1']  # Android driver doesn't support "Select" class. Haven't found workaround.
                           # iPhone 5 used to have an unrelated bug where a screen size refresh mid-test causes this to fail.
                           # Is this bug still on iPhone 6?

    def body(self):
        # Load Shabbat TOC and scroll to bottom
        self.load_text_toc("Shabbat").scroll_nav_panel_to_bottom()

        # Check that DL Button is visible and not clickable
        visible = self.driver.execute_script(
            'var butt = document.getElementsByClassName("downloadButtonInner")[0]; ' +\
            'var butt_bot = butt.getBoundingClientRect().top + butt.getBoundingClientRect().height; ' +\
            'var win_height = window.innerHeight; ' +\
            'return win_height > butt_bot;'
        )
        assert visible, "Download button below page"
        # This isn't sufficient - it only checks if it's visible in the DOM
        #WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".downloadButtonInner")))

        WebDriverWait(self.driver, TEMPER).until(invisibility_of_element_located((By.CSS_SELECTOR, '.dlVersionFormatSelect + a')))

        # Select version and format
        select1 = Select(self.driver.find_element_by_css_selector('.dlVersionTitleSelect'))
        select1.select_by_value("Wikisource Talmud Bavli/he")
        select2 = Select(self.driver.find_element_by_css_selector('.dlVersionFormatSelect'))
        select2.select_by_value("csv")

        # Check that DL button is clickable
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '.dlVersionFormatSelect + a')))


class LoadSearchFromURL(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_search_url("Passover")


class ClickVersionedSearchResultDesktop(AtomicTest):
    suite_class = DeepReaderSuite
    single_panel = False

    def body(self):
        self.search_for("they howl like dogs")
        versionedResult = self.driver.find_element_by_css_selector('a[href="/Psalms.59.7/en/The_Rashi_Ketuvim_by_Rabbi_Shraga_Silverstein?qh=they howl like dogs"]')
        versionedResult.click()
        WebDriverWait(self.driver, TEMPER).until(staleness_of(versionedResult))
        assert "Psalms.59.7/en/The_Rashi_Ketuvim_by_Rabbi_Shraga_Silverstein" in self.driver.current_url, self.driver.current_url


class CollectionsPagesLoad(AtomicTest):
    suite_class = PageloadSuite
    every_build = True

    def body(self):
        self.load_url("/collections", ".collectionListing")
        self.login_user()
        self.load_url("/collections/new", "#editCollectionPage .field")
        self.load_url("/collections/bimbam", ".collectionPage .sheet")


class BrowserBackAndForward(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    exclude = ['FF/x12', 'FF/x13', 'Sf/x11', 'Sf/x12', 'Sf/x13'] # Buggy handling of Back button

    def body(self):
        # Sidebar
        self.browse_to_ref("Amos 3").click_segment("Amos 3:1").click_category_filter("Commentary")
        assert "Amos.3.1" in self.driver.current_url, self.driver.current_url
        assert "with=Commentary" in self.driver.current_url, self.driver.current_url
        self.driver.back()
        assert "Amos.3.1" in self.driver.current_url, self.driver.current_url
        assert "with=all" in self.driver.current_url, self.driver.current_url
        self.driver.back()
        assert "Amos.3" in self.driver.current_url, self.driver.current_url
        assert "with=" not in self.driver.current_url, self.driver.current_url
        self.driver.forward()
        assert "Amos.3.1" in self.driver.current_url, self.driver.current_url
        assert "with=all" in self.driver.current_url, self.driver.current_url
        self.driver.forward()
        assert "Amos.3.1" in self.driver.current_url, self.driver.current_url
        assert "with=Commentary" in self.driver.current_url, self.driver.current_url
        # Todo - infinite scroll, nav pages, display options, ref normalization

        self.click_segment_to_close_commentary("Amos 3:1")  # Close commentary window on mobile


class ClickVersionedSearchResultMobile(AtomicTest):
    suite_class = DeepReaderSuite
    multi_panel = False

    def body(self):
        hamburger = self.driver.find_element_by_css_selector(".readerNavMenuMenuButton")
        if hamburger:
            hamburger.click()
            wait = WebDriverWait(self.driver, TEMPER)
            wait.until(staleness_of(hamburger))
        self.search_for("Dogs")
        versionedResult = self.driver.find_element_by_css_selector('a[href="/Psalms.59.7/en/The_Rashi_Ketuvim_by_Rabbi_Shraga_Silverstein?qh=Dogs"]')
        versionedResult.click()
        WebDriverWait(self.driver, TEMPER).until(staleness_of(versionedResult))
        assert "Psalms.59.7/en/The_Rashi_Ketuvim_by_Rabbi_Shraga_Silverstein" in self.driver.current_url, self.driver.current_url


class SaveNewSourceSheet(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    single_panel = False  # No source sheets on mobile

    def body(self):
        self.login_user()
        self.nav_to_sheets()

        textBox = self.driver.find_element_by_css_selector("#inlineAdd")

        textBox.send_keys("Genesis")
        WebDriverWait(self.driver, TEMPER).until(
            one_of_these_texts_present_in_element((By.ID, "inlineAddDialogTitle"), ["Enter a", "ENTER A"]))

        textBox.send_keys(" 1")
        WebDriverWait(self.driver, TEMPER).until(
            one_of_these_texts_present_in_element((By.ID, "inlineAddDialogTitle"), ["to continue or", "TO CONTINUE OR"]))

        textBox.send_keys(":9")
        WebDriverWait(self.driver, TEMPER).until(
            one_of_these_texts_present_in_element((By.ID, "inlineAddDialogTitle"), ["to continue or enter a range", "TO CONTINUE OR ENTER A RANGE"]))

        self.driver.find_element_by_css_selector("#inlineAddSourceOK").click()

        WebDriverWait(self.driver, TEMPER).until(element_to_be_clickable((By.CSS_SELECTOR, "#save")))
        saveButton = self.driver.find_element_by_css_selector('#save')
        saveButton.click()

        try:
            # this is site language dependent. try both options
            WebDriverWait(self.driver, TEMPER).until(title_contains("New Source Sheet | Sefaria"))
        except TimeoutException:
            WebDriverWait(self.driver, TEMPER).until(title_contains("דף מקורות חדש | ספריא"))

        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '.headerNavSection .library')))


'''
# Not sure why this isn't working.
class LoginOnMobile(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    multi_panel = False  # Login is tested as part of SaveNewSourceSheet on multipanel

    def body(self):
        self.login_user()
        WebDriverWait(self.driver, TEMPER).until(element_to_be_clickable((By.CSS_SELECTOR, ".accountLinks .account")))

'''


class SpecialCasedSearchBarNavigations(AtomicTest):
    suite_class = ReaderSuite
    every_build = True
    single_panel = False  # This hasn't yet been implemented on mobile

    def body(self):
        self.type_in_search_box("Shabbat")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".readerTextTableOfContents")))
        self.type_in_search_box("Shabbat 12b")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".segment")))
        self.type_in_search_box("Yosef Giqatillah")
        WebDriverWait(self.driver, TEMPER).until(title_contains("Yosef Giqatillah"))
        self.type_in_search_box("Midrash")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".readerNavCategoryMenu")))

        self.type_in_search_box("שבת")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".readerTextTableOfContents")))
        self.type_in_search_box("שבת י״ד")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".segment")))
        self.type_in_search_box("יוסף שאול נתנזון")
        WebDriverWait(self.driver, TEMPER).until(title_contains("Yosef"))
        self.type_in_search_box("מדרש")
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, ".readerNavCategoryMenu")))


class EditorPagesLoad(AtomicTest):
    #todo: build a no-load reader test to match this
    suite_class = PageloadSuite
    every_build = True
    single_panel = False

    def body(self):
        self.load_toc()
        #logged in stuff
        self.login_user()
        self.load_translate("Shabbat 43b")
        # self.load_edit("Genesis 1", "en", "Sefaria Community Translation") -- need debugging, threw a 500 on travis, works local
        self.load_add("Mishnah Peah 4")


class ScrollToHighlight(AtomicTest):
    suite_class = PageloadSuite
    every_build = True    

    def test_by_load(self, ref):
        self.load_ref(ref)
        el = self.driver.find_element_by_css_selector('[data-ref="{}"]'.format(ref))
        assert self.is_element_visible_in_viewport(el)

    def test_in_app(self, ref):
        self.search_ref(ref)
        el = self.driver.find_element_by_css_selector('[data-ref="{}"]'.format(ref))
        assert self.is_element_visible_in_viewport(el)

    def body(self):
        # Test from fresh load, target originally above fold
        self.test_by_load("Kol Bo 130:2")
        # Fresh load, target originally below fold
        self.test_by_load("Kol Bo 3:14")
        # In app, target not in cache
        self.test_in_app("Mishnah Peah 3:3")
        # In app, target in cache
        self.test_in_app("Kol Bo 3:14")


class InfiniteScrollUp(AtomicTest):
    suite_class = ReaderSuite
    every_build = True

    def test_up(self, start_ref, prev_segment_ref):
        from urllib.parse import quote_plus
        self.browse_to_ref(start_ref)
        time.sleep(.5)
        self.scroll_reader_panel_down(100) # This jiggle feels like cheating, but I am finding that a single scroll doesn't trigger the "scroll" event, causing the next scroll to be ignore (with this.justScrolled flag)
        self.scroll_reader_panel_up(200)
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '[data-ref="%s"]' % prev_segment_ref)))
        time.sleep(.5)
        # Wait then check that URL has not changed as a proxy for checking that visible scroll position has not changed
        assert quote_plus(Ref(start_ref).url()) in self.driver.current_url, self.driver.current_url

    def body(self):
        # Simple Text
        self.test_up("Joshua 22", "Joshua 21:45")
        # Complex Text
        self.test_up("Pesach Haggadah, Magid, The Four Sons", "Pesach Haggadah, Magid, Story of the Five Rabbis 2")


class InfiniteScrollDown(AtomicTest):
    suite_class = ReaderSuite
    every_build = True

    def test_down(self, start_ref, next_segment_ref):
        self.browse_to_ref(start_ref).scroll_reader_panel_to_bottom()
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '[data-ref="%s"]' % next_segment_ref)))

    def body(self):
        # Simple Text
        self.test_down("Joshua 22", "Joshua 23:1")
        # Complex Text
        self.test_down("Pesach Haggadah, Magid, The Four Sons", "Pesach Haggadah, Magid, Yechol Me'rosh Chodesh 1")


class BackRestoresScrollPosition(AtomicTest):
    suite_class = ReaderSuite
    every_build = True

    def body(self):
        SCROLL_DISTANCE = 200

        # TOC
        self.load_toc()
        self.scroll_content_to_position(SCROLL_DISTANCE)
        time.sleep(0.4)
        self.click_toc_category("Midrash")
        self.driver.back()
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '[data-cat="Midrash"]')))
        assert self.get_content_scroll_position() == SCROLL_DISTANCE

        # Search
        self.search_for("restoration")
        self.scroll_content_to_position(SCROLL_DISTANCE)
        time.sleep(0.4)
        versionedResult = self.driver.find_element_by_css_selector('a[href="/Mishneh_Torah%2C_Kings_and_Wars.12.2?ven=Yad-Hachazakah,_edited_by_Elias_Soloweyczik%3B_London,_1863&qh=restoration"]')
        versionedResult.click()
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '.segment')))
        self.driver.back()
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '.text_result')))
        assert self.get_content_scroll_position() == SCROLL_DISTANCE

        # Topic
        self.load_topic_page("wonders")
        self.scroll_content_to_position(SCROLL_DISTANCE)
        time.sleep(0.4)
        source = self.driver.find_element_by_css_selector('.storyTitle a')
        source.click()
        WebDriverWait(self.driver, TEMPER).until(visibility_of_element_located((By.CSS_SELECTOR, '.segment')))
        self.driver.back()
        assert self.get_content_scroll_position() == SCROLL_DISTANCE


"""
# Not complete

class LoadRefAndOpenLexicon(AtomicTest):
    suite_class = ReaderSuite
    single_panel = False

    def body(self):
        self.load_ref("Numbers 25:5", lang="he").click_segment("Numbers 25:5")
        assert "Numbers.25.5" in self.driver.current_url, self.driver.current_url
        assert "with=all" in self.driver.current_url, self.driver.current_url
        selector = '.segment[data-ref="{}"] > span.he'.format("Numbers 25:5")
        self.driver.execute_script(
            "var range = document.createRange();" +
            "var start = document.querySelectorAll('[data-ref=\"Numbers 25:5\"]');" +
            "var textNode = start.querySelectorAll('span.he')[0].firstChild;" +
            "range.setStart(textNode, 0);" +
            "range.setEnd(textNode, 5);" +
            "window.getSelection().addRange(range);"
        )
        from selenium.webdriver import ActionChains
        actions = ActionChains(self.driver)
        element = self.driver.find_element_by_css_selector(selector)
        actions.move_to_element(element)
        actions.double_click(on_element=element)
        actions.move_by_offset(50, 0)
        actions.click_and_hold(on_element=None)
        actions.move_by_offset(70, 0)
        actions.release(on_element=None)
        actions.perform()
        WebDriverWait(self.driver, TEMPER).until(element_to_be_clickable((By.CSS_SELECTOR, ".lexicon-content")))

"""
