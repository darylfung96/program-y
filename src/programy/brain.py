"""
Copyright (c) 2016-17 Keith Sterling http://www.keithsterling.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import logging
import re
import xml.etree.ElementTree as ET
try:
    import _pickle as pickle
except:
    import pickle
import gc

from programy.processors.processing import ProcessorLoader
from programy.config.sections.brain.brain import BrainConfiguration
from programy.mappings.denormal import DenormalCollection
from programy.mappings.gender import GenderCollection
from programy.mappings.maps import MapCollection
from programy.mappings.normal import NormalCollection
from programy.mappings.person import PersonCollection
from programy.mappings.properties import PropertiesCollection
from programy.mappings.sets import SetCollection
from programy.dynamic.dynamics import DynamicsCollection
from programy.rdf.collection import RDFCollection
from programy.parser.aiml_parser import AIMLParser
from programy.utils.services.service import ServiceFactory
from programy.utils.text.text import TextUtils
from programy.utils.classes.loader import ClassLoader
import datetime


class Brain(object):
    def __init__(self, configuration: BrainConfiguration):
        self._configuration = configuration
        self._aiml_parser = AIMLParser(self)

        self._denormal_collection = DenormalCollection()
        self._normal_collection = NormalCollection()
        self._gender_collection = GenderCollection()
        self._person_collection = PersonCollection()
        self._person2_collection = PersonCollection()
        self._rdf_collection = RDFCollection()
        self._sets_collection = SetCollection()
        self._maps_collection = MapCollection()
        self._properties_collection = PropertiesCollection()

        self._preprocessors = ProcessorLoader()
        self._postprocessors = ProcessorLoader()

        self._authentication = None
        self._authorisation = None

        self._default_oob = None
        self._oob = {}

        self._regex_templates = {}

        self._dynamics_collection = DynamicsCollection()

        self.load(self._configuration)

    @property
    def configuration(self):
        return self._configuration

    @property
    def aiml_parser(self):
        return self._aiml_parser

    @property
    def denormals(self):
        return self._denormal_collection

    @property
    def normals(self):
        return self._normal_collection

    @property
    def genders(self):
        return self._gender_collection

    @property
    def persons(self):
        return self._person_collection

    @property
    def person2s(self):
        return self._person2_collection

    @property
    def rdf(self):
        return self._rdf_collection

    @property
    def sets(self):
        return self._sets_collection

    @property
    def maps(self):
        return self._maps_collection

    @property
    def properties(self):
        return self._properties_collection

    @property
    def preprocessors(self):
        return self._preprocessors

    @property
    def postprocessors(self):
        return self._postprocessors

    @property
    def authentication(self):
        return self._authentication

    @property
    def authorisation(self):
        return self._authorisation

    @property
    def default_oob(self):
        return self._default_oob

    @property
    def oobs(self):
        return self._oob

    @property
    def regex_templates(self):
        return self._regex_templates

    @property
    def dynamics(self):
        return self._dynamics_collection

    def load_binary(self, brain_configuration):
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading binary brain from [%s]" % brain_configuration.binaries.binary_filename)
        try:
            start = datetime.datetime.now()
            gc.disable()
            f = open(brain_configuration.binaries.binary_filename, "rb")
            self._aiml_parser = pickle.load(f)
            gc.enable()
            f.close()
            stop = datetime.datetime.now()
            diff = stop - start
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Brain load took a total of %.2f sec" % diff.total_seconds())
            load_aiml = False
        except Exception as e:
            logging.exception(e)
            if brain_configuration.binaries.load_aiml_on_binary_fail is True:
                load_aiml = True
            else:
                raise e

    def load_aiml(self, brain_configuration):
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading aiml source brain")
        self._aiml_parser.load_aiml(brain_configuration)

    def save_binary(self, brain_configuration):
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Saving binary brain to [%s]" % brain_configuration.binaries.binary_filename)
        start = datetime.datetime.now()
        f = open(brain_configuration.binaries.binary_filename, "wb")
        pickle.dump(self._aiml_parser, f)
        f.close()
        stop = datetime.datetime.now()
        diff = stop - start
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Brain save took a total of %.2f sec" % diff.total_seconds())

    def load(self, brain_configuration: BrainConfiguration):

        if brain_configuration.binaries.load_binary is True:
            self.load_binary(brain_configuration)

        self.load_aiml(brain_configuration)

        if brain_configuration.binaries.save_binary is True:
            self.save_binary(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading collections")
        self.load_collections(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading services")
        self.load_services(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading security services")
        self.load_security_services(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading oob processors")
        self.load_oob_processors(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading regex templates")
        self.load_regex_templates(brain_configuration)

        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading dynamics sets, maps and vars")
        self.load_dynamics(brain_configuration)

    def _load_denormals(self, brain_configuration):
        if brain_configuration.files.denormal is not None:
            total = self._denormal_collection.load_from_filename(brain_configuration.files.denormal)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d denormalisations", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for denormal")

    def _load_normals(self, brain_configuration):
        if brain_configuration.files.normal is not None:
            total = self._normal_collection.load_from_filename(brain_configuration.files.normal)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d normalisations", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for normal")

    def _load_genders(self, brain_configuration):
        if brain_configuration.files.gender is not None:
            total = self._gender_collection.load_from_filename(brain_configuration.files.gender)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d genderisations", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for gender")

    def _load_persons(self, brain_configuration):
        if brain_configuration.files.person is not None:
            total = self._person_collection.load_from_filename(brain_configuration.files.person)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d persons", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for person")

    def _load_person2s(self, brain_configuration):
        if brain_configuration.files.person2 is not None:
            total = self._person2_collection.load_from_filename(brain_configuration.files.person2)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d person2s", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for person2")

    def _load_properties(self, brain_configuration):
        if brain_configuration.files.properties is not None:
            total = self._properties_collection.load_from_filename(brain_configuration.files.properties)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d properties", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for properties")

    def _load_rdf(self, brain_configuration):
        if brain_configuration.files.rdf_files is not None and brain_configuration.files.rdf_files.files is not None:
            total = self._rdf_collection.load(brain_configuration.files.rdf_files)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d rdf files", total)
        elif brain_configuration.files.triples is not None:
            total = self._rdf_collection.load_from_filename(brain_configuration.files.triples)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d triples", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for triples")

    def _load_sets(self, brain_configuration):
        total = self._sets_collection.load(brain_configuration.files.set_files)
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d sets files", total)

    def _load_maps(self, brain_configuration):
        total = self._maps_collection.load(brain_configuration.files.map_files)
        if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d maps files", total)

    def _load_preprocessors(self, brain_configuration):
        if brain_configuration.files.preprocessors is not None:
            total = self._preprocessors.load(brain_configuration.files.preprocessors)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d pre processors", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for pre processors")

    def _load_postprocessors(self, brain_configuration):
        if brain_configuration.files.postprocessors is not None:
            total = self._postprocessors.load(brain_configuration.files.postprocessors)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d post processors", total)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("No configuration setting for post processors")

    def load_collections(self, brain_configuration):
        self._load_denormals(brain_configuration)
        self._load_normals(brain_configuration)
        self._load_genders(brain_configuration)
        self._load_persons(brain_configuration)
        self._load_person2s(brain_configuration)
        self._load_properties(brain_configuration)
        self._load_rdf(brain_configuration)
        self._load_sets(brain_configuration)
        self._load_maps(brain_configuration)
        self._load_preprocessors(brain_configuration)
        self._load_postprocessors(brain_configuration)

    def load_services(self, brain_configuration):
        ServiceFactory.preload_services(brain_configuration.services)

    def load_security_services(self, brain_configuration):
        if brain_configuration.security is not None:
            if brain_configuration.security.authentication is not None:
                if brain_configuration.security.authentication.classname is not None:
                    try:
                        classobject = ClassLoader.instantiate_class(
                            brain_configuration.security.authentication.classname)
                        self._authentication = classobject(brain_configuration.security.authentication)
                    except Exception as excep:
                        logging.exception(excep)
            else:
                if logging.getLogger().isEnabledFor(logging.DEBUG): logging.debug("No authentication configuration defined")

            if brain_configuration.security.authorisation is not None:
                if brain_configuration.security.authorisation.classname is not None:
                    try:
                        classobject = ClassLoader.instantiate_class(
                            brain_configuration.security.authorisation.classname)
                        self._authorisation = classobject(brain_configuration.security.authorisation)
                    except Exception as excep:
                        logging.exception(excep)
            else:
                if logging.getLogger().isEnabledFor(logging.DEBUG): logging.debug("No authorisation configuration defined")

        else:
            if logging.getLogger().isEnabledFor(logging.DEBUG): logging.debug("No security configuration defined, running open...")

    def load_dynamics(self, brain_configuration):
        if brain_configuration.dynamics is not None:
            self._dynamics_collection.load_from_configuration(brain_configuration.dynamics)
        else:
            if logging.getLogger().isEnabledFor(logging.DEBUG): logging.debug("No dynamics configuration defined...")

    def pre_process_question(self, bot, clientid, question):
        return self.preprocessors.process(bot, clientid, question)

    def parse_last_sentences_from_response(self, response):
        response = re.sub(r'<\s*br\s*/>\s*', ".", response)
        response = re.sub(r'<br></br>*', ".", response)
        sentences = response.split(".")
        sentences = [x for x in sentences if x]
        last_sentence = sentences[-1]
        that_pattern = TextUtils.strip_all_punctuation(last_sentence)
        that_pattern = that_pattern.strip()
        return that_pattern

    def load_oob_processors(self, brain_configuration):
        if brain_configuration.oob is not None:
            if brain_configuration.oob.default() is not None:
                try:
                    if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading default oob")
                    classobject = ClassLoader.instantiate_class(brain_configuration.oob.default().classname)
                    self._default_oob = classobject()
                except Exception as excep:
                    logging.exception(excep)

            for oob_name in  brain_configuration.oob.oobs():
                try:
                    if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loading oob: %s"%oob_name)
                    classobject = ClassLoader.instantiate_class(brain_configuration.oob.oob(oob_name).classname)
                    self._oob[oob_name] = classobject()
                except Exception as excep:
                    logging.exception(excep)

    def load_regex_templates(self, brain_configuration):
        if brain_configuration.files.regex_templates is not None:
            collection = PropertiesCollection ()
            total = collection.load_from_filename(brain_configuration.files.regex_templates)
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Loaded a total of %d regex templates", total)

            for pair in collection.pairs:
                name = pair[0]
                pattern = pair[1]
                try:
                    self._regex_templates[name] = re.compile(pattern)
                except Exception:
                    if logging.getLogger().isEnabledFor(logging.INFO): logging.error("Invalid regex template [%s]"%pattern)

    def regex_template(self, name):
        if name in self._regex_templates:
            return self._regex_templates[name]
        else:
            return None

    def strip_oob(self, response):
        m = re.compile("(.*)(<\s*oob\s*>.*<\/\s*oob\s*>)(.*)")
        g = m.match(response)
        if g is not None:
            front =  g.group(1).strip()
            back = g.group(3).strip()
            response = ""
            if front != "":
                response = front + " "
            response += back
            oob = g.group(2)
            return response, oob
        return response, None

    def process_oob(self, bot, clientid, oob_command):

        oob_content = ET.fromstring(oob_command)

        if oob_content.tag == 'oob':
            for child in oob_content.findall('./'):
                if child.tag in self._oob:
                    oob_class = self._oob[child.tag]
                    return oob_class.process_out_of_bounds(bot, clientid, child)
                else:
                    return self._default_oob.process_out_of_bounds(bot, clientid, child)

        return ""

    def post_process_response(self, bot, clientid, response: str):
        return self.postprocessors.process(bot, clientid, response)

    def dump_tree(self):
        self._aiml_parser.pattern_parser.root.dump(tabs="")

    def ask_question(self, bot, clientid, sentence, srai=False, brain_question_context=None):

        if brain_question_context is not None:
            brain_question_context.clientid = clientid
            brain_question_context.srai = srai
            brain_question_context.sentence = sentence

        if self.authentication is not None:
            if self.authentication.authenticate(clientid) is False:
                if logging.getLogger().isEnabledFor(logging.ERROR): logging.error("[%s] failed authentication!")
                return self.authentication.configuration.denied_srai

        conversation = bot.get_conversation(clientid)

        topic_pattern = conversation.property("topic")
        if topic_pattern is None:
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("No Topic pattern default to [*]")
            topic_pattern = "*"
        else:
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("Topic pattern = [%s]", topic_pattern)

        if brain_question_context is not None:
            brain_question_context.topic = topic_pattern

        try:
            that_question = conversation.previous_nth_question(1)
            that_sentence = that_question.current_sentence()

            # If the last response was valid, i.e not none and not empty string, then use
            # that as the that_pattern, otherwise we default to '*' as pattern
            if that_sentence.response is not None and that_sentence.response != '':
                that_pattern = self.parse_last_sentences_from_response(that_sentence.response)
                if logging.getLogger().isEnabledFor(logging.INFO): logging.info("That pattern = [%s]", that_pattern)
            else:
                if logging.getLogger().isEnabledFor(logging.INFO): logging.info("That pattern, no response, default to [*]")
                that_pattern = "*"

        except Exception:
            if logging.getLogger().isEnabledFor(logging.INFO): logging.info("No That pattern default to [*]")
            that_pattern = "*"

        if brain_question_context is not None:
            brain_question_context.that = that_pattern

        match_context = self._aiml_parser.match_sentence(bot, clientid,
                                                         sentence,
                                                         topic_pattern=topic_pattern,
                                                         that_pattern=that_pattern)

        if match_context is not None:

            if brain_question_context is not None:
                brain_question_context.match_context = match_context

            template_node = match_context.template_node()
            if logging.getLogger().isEnabledFor(logging.DEBUG): logging.debug("AIML Parser evaluating template [%s]", template_node.to_string())
            response = template_node.template.resolve(bot, clientid)

            if brain_question_context is not None:
                brain_question_context.raw_response = response

            if "<oob>" in response:
                response, oob = self.strip_oob(response)
                if oob is not None:
                    oob_response = self.process_oob(bot, clientid, oob)

                    if brain_question_context is not None:
                        brain_question_context.raw_response = response
                        brain_question_context.oob_response = oob_response

                    response = response + " " + oob_response

            return response

        return None

