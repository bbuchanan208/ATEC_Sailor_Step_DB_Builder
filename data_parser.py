import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join


class DataParser:

    def __init__(self, kinect_text_file_path):
        self.kinect_text_file_path = kinect_text_file_path
        self.left_foot_positions = []
        self.right_foot_positions = []
        self.gradient_textfile_array = []
        self.feet_textfile_array = []
        self.bulk_data = self._textfile_to_array(kinect_text_file_path)
        self._confirm_text_file_is_seqential()
        self._confirm_text_file_one_subject()
        self._get_all_right_foot_positions()
        self._get_all_left_foot_positions()
        self._build_gradient_textfile_array()
        self.segment = int(kinect_text_file_path[-6:-4])
        # self._build_left_right_foot_textfile_array() This isbroken

    def _get_base_name(self):
        pass

    def zero_ref_array(self, array_in):
        start = array_in[0]
        array_out = []
        for entry in array_in:
            array_out.append(self._format_x_coord(float(entry) - float(start)))
        return array_out

    def _format_x_coord(self, x_coord, rounding_dig=5):
        return str((round(float(x_coord), rounding_dig)))

    def _confirm_text_file_is_seqential(self):
        e = 0
        last = -1
        while e < len(self.bulk_data):
            if (int(self.bulk_data[e][0]) != (last + 1)):
                raise Exception("File is not sequential on frame " + str(last) + " on line " + str(e + 1) + " in " +
                                str(self.kinect_text_file_path))
            last += 1
            e += 52

    def _confirm_text_file_one_subject(self):
        e = 53
        subject_number = int(self.bulk_data[e][0])
        while e < len(self.bulk_data):
            if (int(self.bulk_data[e][0]) != (subject_number)):
                print("Incorrect Subject number on line " + str(e))
                raise Exception(e)
            e += 52

    def _get_all_left_foot_positions(self, x_coord_only=True):
        self.left_foot_positions.append(self.bulk_data[17][0])
        i = 69
        while i < len(self.bulk_data):
            if x_coord_only is True:
                self.left_foot_positions.append(self.bulk_data[i][0])
            else:
                self.left_foot_positions.append(self.bulk_data[i])
            i += 52
        # self.left_foot_positions = self.zero_ref_array(self.left_foot_positions)

    def _get_all_right_foot_positions(self, x_coord_only=True):
        self.right_foot_positions.append(self.bulk_data[21][0])
        i = 73
        while i < len(self.bulk_data):
            if x_coord_only is True:
                self.right_foot_positions.append(self.bulk_data[i][0])
            else:
                self.right_foot_positions.append(self.bulk_data[i])
            i += 52
        # self.right_foot_positions = self.zero_ref_array(self.right_foot_positions)

    def _build_gradient_textfile_array(self, make_graph=False):
        left_feet = np.array(self.left_foot_positions, dtype=float, )
        right_feet = np.array(self.right_foot_positions, dtype=float)
        left_feet_gradient = np.gradient(left_feet)
        right_feet_gradient = np.gradient(right_feet)
        self.left_feet_gradient = left_feet_gradient
        self.right_feet_gradient = right_feet_gradient
        for i in range(len(left_feet_gradient)):
            self.gradient_textfile_array.append(str(self._format_x_coord(left_feet_gradient[i])) + " " +
                                                str(self._format_x_coord(right_feet_gradient[i])))
        if make_graph: self.make_graph(left_feet_gradient, right_feet_gradient)

    def _build_left_right_foot_textfile_array(self, make_graph=False):
        left = self.zero_ref_array(self.left_foot_positions)
        right = self.zero_ref_array(self.right_foot_positions)
        print(left)
        print(right)
        self.feet_textfile_array = [str(self.left_foot_positions[i]) + " " + str(self.right_foot_positions[i])
                                    for i in range(len(self.left_foot_positions))]
        self.feet_textfile_array.append()
        if make_graph: self.make_graph(left, right)

    def _textfile_to_array(self, text_file_path):
        return_list = []
        text_file = open(text_file_path, "r")
        for line in text_file:
            return_list.append(line.split())
        return return_list

    def make_graph(self, y_left, y_right):
        X = [i for i in range(1, len(y_left) + 1)]
        max_of = max(max(y_left), max(y_right))
        min_of = min(min(y_left), min(y_right))
        plt.plot(X, y_left, "g", label="Left foot", lw=0.4)
        plt.plot(X, y_right, "c", label="Right foot", lw=0.4)
        plt.ylim(bottom=min_of, top=max_of)
        plt.legend(loc="best")
        plt.show()
        plt.clf()


class AnnotationParser:

    def __init__(self, annotation_file_location):
        self.timestamps = []
        self.annotations = []
        self._get_info_from_file(annotation_file_location)

    def _get_info_from_file(self, annotation_file_location):
        with open(annotation_file_location) as my_file:
            file_array = [e[:-1] for e in my_file]
        file_array = [e.split(' ') for e in file_array]
        self.duration = float(file_array[0][0])
        self.offset = float(file_array[0][1])
        for entry in file_array[1:]:
            self.timestamps.append(entry[0][6:])
            self.annotations.append(entry[1])


class SingleFileBuilder:

    def __init__(self, annotation_file_loc, kinect_file_location):
        foo = DataParser(kinect_file_location)
        self.left_grad = foo.left_feet_gradient
        self.right_grad = foo.right_feet_gradient
        self.segment = foo.segment
        self.sub_visit = str(kinect_file_location[7:]).split('t')[0]
        self.task_number = str(kinect_file_location[-6:-4])
        bar = AnnotationParser(annotation_file_loc)
        self.annotations = bar.annotations
        self.timestamps = bar.timestamps
        self.entries = []
        self._build_entries()

    def _get_frame_num_from_timestamp(self, timestamp):
        return round(float(timestamp) * 30)

    def _get_space_separated_gradient(self, timestamp, left=False, right=False, round_to=3):
        """
        Takes a timestamp as in input and outputs the 45 frames after that timestamp
        :param timestamp:
        :return:
        """
        return_string = ''
        starting_frame = self._get_frame_num_from_timestamp(timestamp)
        if left:
            for gradients in self.left_grad[starting_frame: starting_frame + 45]:
                return_string += str(round(float(gradients), round_to))
                return_string += ' '
        elif right:
            for gradients in self.right_grad[starting_frame: starting_frame + 45]:
                return_string += str(round(float(gradients), round_to))
                return_string += ' '
        else:
            raise Exception('Left or Right not selected')
        return return_string[:-1]
        # If the extra space is not wanted return what is below instead
        # return return_string[:-1]

    def _build_entries(self):
        """
        Build an entry for the database with the following header:
        Subject and visit name, timestamp, annotation, left foot gradient, right foot gradient
        :return:
        """
        for index in range(len(self.timestamps)):
            entry_to_add = []
            entry_to_add.append(self.sub_visit)
            entry_to_add.append(self.task_number)
            entry_to_add.append(str(index + 1))
            timestamp = self.timestamps[index]
            entry_to_add.append(timestamp)
            entry_to_add.append(self.annotations[index])
            entry_to_add.append(self._get_space_separated_gradient(timestamp, left=True))
            entry_to_add.append(self._get_space_separated_gradient(timestamp, right=True))
            self.entries.append(entry_to_add)


class BulkDBBuilder:
    """
    The only class that should be called.
    In order to function properly:
        1. All of the annotations should be placed in a folder called 'annotations'
        2. Everything in that folder needs to have the following file naming convention
            Example: ATEC_05-V1-052418_task20.txt.txt
            05 is the subject number
            V1 is the visit number, this will only be V1 or V2
            task_20 or task_21
        3. All of the kinect files need to be placed in a folder called 'kinect'
             Example: 5v2t20.txt
             5v2 is the subject and visit number
             20 is the task number
             The 't' needs to be there to seperate the subject/visit info from the task number

    The class will search for kinect info based on the annotation folder
    All the user will have to do is instantiate the class and call build_db_csv_file()
    """

    def __init__(self):
        self.kinect_files_list = self._get_files_in_directory(kinect=True)
        self.annotation_files_list = self._get_files_in_directory(annotations=True)
        self.list_of_entries = []

    def build_db_csv_file(self):
        for file_name in self.annotation_files_list:
            file_to_search_for = self._convert_annotation_name_to_kinect_name(file_name)
            if file_to_search_for in self.kinect_files_list:
                annotation_location = 'annotations/' + file_name
                kinect_location = 'kinect/' + file_to_search_for
                temp_obj = SingleFileBuilder(annotation_location, kinect_location)
                self.list_of_entries += temp_obj.entries
        self._save_array_to_text_file('ATEC_Sailor_Step_DB.csv', self.list_of_entries)

    def _get_files_in_directory(self, kinect=False, annotations=False):
        if kinect:
            return [f for f in listdir('kinect') if isfile(join('kinect', f))]
        elif annotations:
            return [f for f in listdir('annotations') if isfile(join('annotations', f))]
        else:
            raise Exception('Parameter not selected')

    def _convert_annotation_name_to_kinect_name(self, file_name):
        subject_num = str(int(file_name[5:7]))
        visit_num = str(int(file_name[9:10]))
        task_num = str(int(file_name[-10:-8]))
        return subject_num + 'v' + visit_num + 't' + task_num + '.txt'

    def _convert_list_to_string(self, entry_list):
        return_string = ""
        for item in entry_list:
            return_string += str(item)
            return_string += ","
        return return_string[:-1]

    def _save_array_to_text_file(self, save_file_path, list_in):
        file_object = open(save_file_path, "w+")
        file_object.write("Subject_and_visit,task_number,segment,timestamp,annotation,left_foot_gradient,"
                          "right_foot_gradient" + "\n")
        for entry_list in list_in:
            file_object.write(self._convert_list_to_string(entry_list) + "\n")
        file_object.close()


BulkDBBuilder().build_db_csv_file()
