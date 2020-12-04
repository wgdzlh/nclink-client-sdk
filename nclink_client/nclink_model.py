# coding: utf-8

from __future__ import annotations
from enum import Enum
from typing import Dict, List

MS_IN_DAY = 24 * 3600 * 1000


class NclinkNodeType(Enum):
    InvalidNode = 0
    RootNode = 1
    DeviceNode = 2
    ConfigNode = 3
    DataItemNode = 4
    ComponentNode = 5
    SampleChannelNode = 6


class NcLinkValueType(Enum):
    VT_Unknown = 0
    VT_Bool = 1
    VT_Char = 2
    VT_Short = 3
    VT_Int = 4
    VT_Float = 5
    VT_String = 6
    VT_JsonObjString = 7


class NclinkBaseNode:
    def __init__(self, id_='', type_='', name='', node_type=NclinkNodeType.InvalidNode):
        self._id = id_
        self._type = type_
        self._node_type = node_type
        self._parent = None
        self.name = name
        self.path = ''
        self.description = ''

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> str:
        return self._type

    @property
    def node_type(self) -> NclinkNodeType:
        return self._node_type

    @property
    def parent(self) -> NclinkBaseNode:
        return self._parent

    def validate(self) -> bool:
        if self._id and self._type and self.name:
            return True
        return False


class NclinkConfigNode(NclinkBaseNode):
    def __init__(self, id_='', type_='', name=''):
        super().__init__(id_, type_, name, NclinkNodeType.ConfigNode)
        self.value_type = NcLinkValueType.VT_Unknown
        self.int_value = 0
        self.str_value = ''
        self.data_type = ''
        self.settable = False

    @property
    def parent(self) -> NclinkBaseNode:
        return self._parent

    @parent.setter
    def parent(self, val):
        self._parent = val
        if val:
            self.path = f'{self._parent.path}/{self._type}'

    def validate(self) -> bool:
        if not (self.path and super().validate()):
            return False
        if self._parent and (self._parent.node_type == NclinkNodeType.DeviceNode or
                             self._parent.node_type == NclinkNodeType.ComponentNode):
            return True
        return False


class NclinkDataItemNode(NclinkBaseNode):
    def __init__(self, id_='', type_='', name=''):
        super().__init__(id_, type_, name, NclinkNodeType.DataItemNode)
        self.number = ''
        self.data_type = ''
        self.settable = False

    @property
    def parent(self) -> NclinkBaseNode:
        return self._parent

    @parent.setter
    def parent(self, val):
        self._parent = val
        if val and self._type:
            if self.number:
                self.path = f'{self._parent.path}/{self._type}@{self.number}'
            else:
                self.path = f'{self._parent.path}/{self._type}'

    def validate(self) -> bool:
        if self._parent and self.path and super().validate():
            return True
        return False


class NclinkSampleChannelNode(NclinkBaseNode):

    def __init__(self, id_='', type_='', name=''):
        super().__init__(id_, type_, name, NclinkNodeType.SampleChannelNode)
        self._ids = []
        self._sample_point_count = 0
        self._sample_points = {}
        self.sample_interval = 0  # millisecond
        self.upload_interval = 0  # millisecond

    @property
    def parent(self) -> NclinkBaseNode:
        return self._parent

    @parent.setter
    def parent(self, val):
        self._parent = val
        if val:
            self.path = f'{self._parent.path}/{self._type}'

    @property
    def ids(self):
        return self._ids

    @property
    def sample_point_count(self):
        return self._sample_point_count

    def validate(self) -> bool:
        if not (self._parent and self.path and super().validate()):
            return False
        return 0 < self.sample_interval <= MS_IN_DAY and \
            0 < self.upload_interval <= MS_IN_DAY and \
            self.sample_interval <= self.upload_interval

    def add_sample_point(self, sp: NclinkBaseNode) -> bool:
        if sp._id in self._sample_points:
            return False
        if not (sp.node_type == NclinkNodeType.DataItemNode or
                sp.node_type == NclinkNodeType.ConfigNode):
            return False
        self._sample_points[sp._id] = sp
        return True

    def add_sample_point_id(self, id_: str) -> bool:
        if id_ in self._ids:
            return False
        self._ids.append(id_)
        self._sample_point_count += 1
        return True


class NclinkComponentNode(NclinkBaseNode):
    def __init__(self, id_='', type_='', name=''):
        super().__init__(id_, type_, name, NclinkNodeType.ComponentNode)
        self._config_nodes = {}
        self._data_item_nodes = {}
        self._component_nodes = {}
        self.number = ''

    @property
    def parent(self) -> NclinkBaseNode:
        return self._parent

    @parent.setter
    def parent(self, val):
        self._parent = val
        if val and self._type:
            if self.number:
                self.path = f'{self._parent.path}/{self._type}@{self.number}'
            else:
                self.path = f'{self._parent.path}/{self._type}'

    @property
    def config_nodes(self) -> Dict[str, NclinkConfigNode]:
        return self._config_nodes

    @property
    def data_item_nodes(self) -> Dict[str, NclinkDataItemNode]:
        return self._data_item_nodes

    @property
    def component_nodes(self) -> Dict[str, NclinkComponentNode]:
        return self._component_nodes

    def validate(self) -> bool:
        if self._parent and self.path and super().validate():
            return True
        return False

    def add_config_node(self, cn: NclinkConfigNode) -> bool:
        if cn._id in self._config_nodes:
            return False
        self._config_nodes[cn._id] = cn
        return True

    def add_data_item_node(self, din: NclinkDataItemNode) -> bool:
        if din._id in self._data_item_nodes:
            return False
        self._data_item_nodes[din._id] = din
        return True

    def add_component_node(self, cpn: NclinkComponentNode) -> bool:
        if cpn._id in self._component_nodes:
            return False
        self._component_nodes[cpn._id] = cpn
        return True


class NclinkDeviceNode(NclinkBaseNode):
    def __init__(self, id_='', type_='', name='', version=''):
        super().__init__(id_, type_, name, NclinkNodeType.DeviceNode)
        self._version = version
        self._dev_guid = ''

        self._sample_channel_nodes = {}
        self._config_nodes = {}
        self._data_item_nodes = {}
        self._component_nodes = {}

        self._node_dictionary = {}
        self._id_to_path_map = {}
        self._path_to_id_map = {}

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, val):
        self._type = val
        self.path = 'NC_LINK_ROOT/' + val

    @property
    def version(self) -> str:
        return self._version

    @property
    def dev_guid(self) -> str:
        return self._dev_guid

    @dev_guid.setter
    def dev_guid(self, val):
        self._dev_guid = val

    @property
    def sample_channel_nodes(self) -> Dict[str, NclinkSampleChannelNode]:
        return self._sample_channel_nodes

    @property
    def config_nodes(self) -> Dict[str, NclinkConfigNode]:
        return self._config_nodes

    @property
    def data_item_nodes(self) -> Dict[str, NclinkDataItemNode]:
        return self._data_item_nodes

    @property
    def component_nodes(self) -> Dict[str, NclinkComponentNode]:
        return self._component_nodes

    @property
    def id_to_path_map(self) -> Dict[str, str]:
        return self._id_to_path_map

    @property
    def path_to_id_map(self) -> Dict[str, str]:
        return self._path_to_id_map

    def validate(self) -> bool:
        if self.version and self.path and super().validate():
            return True
        return False

    def add_sample_channel_node(self, scn: NclinkSampleChannelNode) -> bool:
        if scn._id in self._sample_channel_nodes:
            return False
        self._sample_channel_nodes[scn._id] = scn
        return True

    def add_config_node(self, cn: NclinkConfigNode) -> bool:
        if cn._id in self._config_nodes:
            return False
        self._config_nodes[cn._id] = cn
        return True

    def add_data_item_node(self, din: NclinkDataItemNode) -> bool:
        if din._id in self._data_item_nodes:
            return False
        self._data_item_nodes[din._id] = din
        return True

    def add_component_node(self, cpn: NclinkComponentNode) -> bool:
        if cpn._id in self._component_nodes:
            return False
        self._component_nodes[cpn._id] = cpn
        return True

    def dump_all_nodes(self) -> str:
        total_cnt = len(self._node_dictionary)
        if total_cnt == 0:
            return '节点集合为空'

        di_cnt = 0
        cfg_cnt = 0
        sc_cnt = 0
        cpn_cnt = 0
        dev_cnt = 0
        invalid_cnt = 0

        res = ['节点集信息:']
        for node_id, node in self._node_dictionary.items():
            res.append(f'\t节点ID: {node_id:10}\t节点PATH: {node.path}')
            t = node.node_type
            if t == NclinkNodeType.DataItemNode:
                di_cnt += 1
            elif t == NclinkNodeType.ConfigNode:
                cfg_cnt += 1
            elif t == NclinkNodeType.SampleChannelNode:
                sc_cnt += 1
            elif t == NclinkNodeType.ComponentNode:
                cpn_cnt += 1
            elif t == NclinkNodeType.DeviceNode:
                dev_cnt += 1
            else:
                invalid_cnt += 1

        res.append(f'---采样通道数:   {sc_cnt}\n'
                   f'---配置节点数:   {cfg_cnt}\n'
                   f'---数据项节点数: {di_cnt}\n'
                   f'---组件节点数:   {cpn_cnt}\n'
                   f'---设备节点数:   {dev_cnt}\n'
                   f'---不明节点数:   {invalid_cnt}\n'
                   f'---节点总数:     {total_cnt}\n')
        return '\n'.join(res)

    def build_maps(self):
        for node in self._node_dictionary.values():
            self._id_to_path_map[node.id] = node.path
            self._path_to_id_map[node.path] = node.id

    def get_all_config_and_data_item_path(self) -> List[str]:
        res = []
        targets = (NclinkNodeType.ConfigNode, NclinkNodeType.DataItemNode)
        for node in self._node_dictionary.values():
            if node.node_type in targets:
                res.append(node.path)
        return res
