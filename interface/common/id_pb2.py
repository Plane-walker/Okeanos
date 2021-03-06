# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: common/id.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='common/id.proto',
  package='common',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0f\x63ommon/id.proto\x12\x06\x63ommon\"\x1b\n\x05\x43hain\x12\x12\n\nidentifier\x18\x01 \x01(\t\"\x1a\n\x04Node\x12\x12\n\nidentifier\x18\x01 \x01(\tb\x06proto3'
)




_CHAIN = _descriptor.Descriptor(
  name='Chain',
  full_name='common.Chain',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='identifier', full_name='common.Chain.identifier', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=27,
  serialized_end=54,
)


_NODE = _descriptor.Descriptor(
  name='Node',
  full_name='common.Node',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='identifier', full_name='common.Node.identifier', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=56,
  serialized_end=82,
)

DESCRIPTOR.message_types_by_name['Chain'] = _CHAIN
DESCRIPTOR.message_types_by_name['Node'] = _NODE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Chain = _reflection.GeneratedProtocolMessageType('Chain', (_message.Message,), {
  'DESCRIPTOR' : _CHAIN,
  '__module__' : 'common.id_pb2'
  # @@protoc_insertion_point(class_scope:common.Chain)
  })
_sym_db.RegisterMessage(Chain)

Node = _reflection.GeneratedProtocolMessageType('Node', (_message.Message,), {
  'DESCRIPTOR' : _NODE,
  '__module__' : 'common.id_pb2'
  # @@protoc_insertion_point(class_scope:common.Node)
  })
_sym_db.RegisterMessage(Node)


# @@protoc_insertion_point(module_scope)
