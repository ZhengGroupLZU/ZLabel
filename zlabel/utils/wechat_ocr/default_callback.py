from .winapi import *


callbacks_def = {
    # static void DefaultReadOnPush(uint32_t request_id, const void* request_info, void* user_data);
    "kMMReadPush": CFUNCTYPE(void, c_uint32, c_void_p, c_void_p),
    # static void DefaultReadOnPull(uint32_t request_id, const void* request_info, void* user_data);
    "kMMReadPull": CFUNCTYPE(void, c_uint32, c_void_p, c_void_p),
    # static void DefaultReadOnShared(uint32_t request_id, const void* request_info, void* user_data);
    "kMMReadShared": CFUNCTYPE(void, c_uint32, c_void_p, c_void_p),
    # static void DefaultRemoteOnConnect(bool is_connected, void* user_data);
    "kMMRemoteConnect": CFUNCTYPE(void, c_bool, c_void_p),
    # static void DefaultRemoteOnDisConnect(void* user_data);
    "kMMRemoteDisconnect": CFUNCTYPE(void, c_void_p),
    # static void DefaultRemoteOnProcessLaunched(void* user_data);
    "kMMRemoteProcessLaunched": CFUNCTYPE(void, c_void_p),
    # static void DefaultRemoteOnProcessLaunchFailed(int error_code, void* user_data);
    "kMMRemoteProcessLaunchFailed": CFUNCTYPE(void, c_int, c_void_p),
    # static void DefaultRemoteOnMojoError(const void* errorbuf, int errorsize, void* user_data);
    "kMMRemoteMojoError": CFUNCTYPE(void, c_void_p, c_int, c_void_p),
}


def DefaultReadPush(request_id: c_uint32, request_info: c_void_p, user_data: py_object): ...


def DefaultReadPull(request_id: c_uint32, request_info: c_void_p, user_data: py_object): ...


def DefaultReadShared(request_id: c_uint32, request_info: c_void_p, user_data: py_object): ...


def DefaultRemoteConnect(is_connected: c_bool, user_data: py_object): ...


def DefaultRemoteDisConnect(user_data: py_object): ...


def DefaultRemoteProcessLaunched(user_data: py_object): ...


def DefaultRemoteProcessLaunchFailed(error_code: c_int, user_data: py_object): ...


def DefaultRemoteMojoError(errorbuf: c_void_p, errorsize: c_int, user_data: py_object): ...
