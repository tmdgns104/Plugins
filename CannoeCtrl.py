import datetime
import os
import glob
from can import Message, Logger, Notifier, broadcastmanager
from can.interfaces.vector import VectorBus

broadcastmanager.USE_WINDOWS_EVENTS = False

class CANoeCtrl:
    def __init__(self, device_info):
        self.bus = []
        dev_dict = eval(device_info)
        for rp in range(0, len(dev_dict)):
            if dev_dict[rp]['is_fd'] is False:
                self.bus.append(VectorBus(channel=dev_dict[rp]['channel'], app_name=dev_dict['app_name'],
                                          bitrate=dev_dict[rp]['biterate'], data_bitrate=dev_dict[rp]['data_bitrate'],
                                          fd=False, receive_own_messages=True))
        else:
            self.bus.append(
                VectorBus(channel=dev_dict[rp]['channel'], app_name=dev_dict['app_name'], bitrate=dev_dict[rp]['biterate'],
                          data_bitrate=dev_dict[rp]['data_bitrate'], sjwAbr=2, rx_queue_size=2 ** 20,
                          receive_own_messages=True))
        self.CANoe_logger = None
        self.CANoe_logger_full = None
        self.CANoe_recv = None


    def canoe_full_log_save_start(self, path, file_name):
        file_name_SD = file_name.split('.')
        log_path = path + file_name_SD[0] + "_{0}.".format(datetime.datetime.now().strftime("%y%m%d_%H%M")) + file_name_SD[
            1]
        self.CANoe_logger_full = Logger(log_path)
        self.CANoe_recv = Notifier(self.bus, [self.CANoe_logger_full])


    def canoe_full_log_save_stop(self):
        for busNum in range(0, len(self.bus)):
            self.bus[busNum].stop_all_periodic_tasks()
        self.CANoe_logger_full_stop()


    def cannoe_log_save_start(self, path, file_name):
        file_name_SD = file_name.split('.')
        log_path = path + file_name_SD[0] + "_{0}.".format(datetime.datetime.now().strftime("%y%m%d_%H%M%S")) + \
                   file_name_SD[1]
        self.CANoe_logger = Logger(loger_path)
        self.CANoe_recv_add_listener(self.CANoe_logger)


    def cannoe_log_save_stop(self):
        self.CANoe_recv.remove_listener(self.CANoe_logger)
        self.CANoe_logger.stop()


    def cannoe_send_msg(self, message_id, cycle_time, can_message, bus_channel, message_type='FD'):
        _message_id = int(message_id, 16)
        _bus_ch = int(bus_channel)

        if message_type == "FD":
            _is_fd = True
        else:
            _is_fd = False

        if _message_id <= 'ox7ff':
            _is_extended_id = False
        else:
            _is_extended_id = True

        _can_message = [int(n, 16) for n in can_message.split()]
        _cycle_time = int(cycle_time)

        if _cycle_time > 0:
            self.bus[_bus_ch].send_preiodic(
                Message(arbitration_id=_message_id,
                        data=_can_message,
                        is_fd=_is_fd,
                        dlc=len(_can_message),
                        is_extended_id=_is_extended_id,
                        is_rx=False), _cycle_time / 1000)
        else:
            self.bus[_bus_ch].send_preiodic(
                Message(arbitration_id=_message_id,
                        data=_can_message,
                        is_fd=_is_fd,
                        dlc=len(_can_message),
                        is_extended_id=_is_extended_id,
                        is_rx=False))


    def find_msg_from_latest_log(self, log_path, message_id, can_message):
        find_data = " "
        list_of_files = glob.glob(log_path + '*')
        latest_file = max(list_of_files, key=os.path.getmtime)

        with open(latest_file) as log_file:
            datafile = log_file.readlines()
        for line in datafile:
            if message_id[2:] in line and can_message in line:
                find_data = line.replace('\n', '')
        log_file.close()

        if find_data != "":
            find_result = "pass"
        else:
            find_result = "fail"

        return find_result, find_data


    def __del__(self):
        for busNum in range(0, len(self.bus)):
            self.bus[busNum].shutdown()



