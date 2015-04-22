#!/bin/env python
# coding: utf-8

"""
Dakara Online protocol generator, by Alejandro Santos
"""

from genpackets import *
from gendefs import *


def write_packets_from(fh, fc, base_name, namespace, P):
    # Namespace
    fh.write("""
namespace {namespace} {{
""".format(namespace=namespace))

    fc.write("""
namespace {namespace} {{
""".format(namespace=namespace))

    # Enum with IDs
    fh.write("""enum {base_name}ID {{ \n""".format(base_name=base_name))
    for i, x in enumerate(P):
        if x:
            fh.write("    {base_name}ID_{name} = {packet_id}".format(base_name=base_name, name=x.name, packet_id=i))
            if i == len(P) - 1:
                fh.write("\n")
            else:
                fh.write(",\n")
    fh.write("""};\n""")

    # Base packet class
    fh.write("""
class {base_name} : public Packet {{
public:
    explicit {base_name}(int id) : Packet(id) {{ }}
}};

{base_name}* {base_name}Factory(clsByteQueue* buffer);

""".format(base_name=base_name))

    # Factory
    fc.write("""
{base_name}* {base_name}Factory(clsByteQueue* buffer) {{
    if (buffer->length() < 1) return 0;
    {base_name} *p = 0;
    int PacketID = buffer->PeekByte();

    switch (PacketID) {{
""".format(base_name=base_name))

    for i, x in enumerate(P):
        if not x: continue
        fc.write("""
        case {i}:
            p = new {name}(buffer);
            break;
""".format(i=i, name=x.name))

    fc.write("""
    }}
    return p;
}}
""".format())

    for i, x in enumerate(P):
        if not x: continue

        header_fields = []
        ctor_fields = ""
        min_byte_count = 0
        ctor_fields_bytequeue = ""
        serialize_fields = ""

        for y in x.args:
            arg_name = y[0]
            arg_type = y[1] & 0xff
            arg_type_str = TYPE_TO_STR[arg_type]
            arg_is_array = ((y[1] & TYPE_ARRAY) == TYPE_ARRAY)
            type_reader_name = TYPE_TO_READER_NAME[arg_type]
            type_writer_name = TYPE_TO_WRITER_NAME[arg_type]

            ctor_fields += ", " + arg_name + "()"

            if arg_is_array:
                array_size=y[2]
                min_byte_count += TYPE_SIZE[arg_type] * array_size
                header_fields.append("    {arg_type_str} {arg_name}[{array_size}]; ".format(arg_type_str=arg_type_str, arg_name=arg_name, array_size=array_size))
                ctor_fields_bytequeue += x.get_ctor_fields_bytequeue_fmt(arg_is_array).format(arg_name=arg_name, type_reader_name=type_reader_name, array_size=array_size)
                serialize_fields += x.get_serialize_fields_fmt(arg_is_array).format(arg_name=arg_name, type_writer_name=type_writer_name, array_size=array_size)
            else:
                min_byte_count += TYPE_SIZE[arg_type]
                header_fields.append("    {arg_type_str} {arg_name}; ".format(arg_type_str=arg_type_str, arg_name=arg_name))
                ctor_fields_bytequeue += x.get_ctor_fields_bytequeue_fmt(arg_is_array).format(arg_name=arg_name, type_reader_name=type_reader_name)
                serialize_fields += x.get_serialize_fields_fmt(arg_is_array).format(arg_name=arg_name, type_writer_name=type_writer_name)

        format_args = {
            'base_name': base_name,
            'name': x.name,
            'header_fields': '\n'.join(header_fields),
            'ctor_fields': ctor_fields,
            'packet_id': i,
            'min_byte_count': min_byte_count,
            'ctor_fields_bytequeue': ctor_fields_bytequeue,
            'serialize_fields': serialize_fields,
        }

        # Individual packet header
        fh.write(x.get_header_fmt().format(**format_args))

        # Packet ctor 1
        fc.write(x.get_ctor1_fmt().format(**format_args))

        # Packet ctor 2
        fc.write(x.get_ctor2_fmt().format(**format_args))

        # Packet serialize
        fc.write(x.get_serialize_fmt().format(**format_args))

        # Dispatcher
        fc.write(x.get_dispatcher_fmt().format(**format_args))

    fh.write("""
class {base_name}Handler {{
public:
    virtual ~{base_name}Handler();

""".format(base_name=base_name))

    fc.write("""
{base_name}Handler::~{base_name}Handler() {{}}

""".format(base_name=base_name))

    for i, x in enumerate(P):
        if not x: continue

        fh.write("""    virtual void handle{name}({name}* p);\n""".format(name=x.name))
        fc.write("""void {base_name}Handler::handle{name}({name}* p){{}}\n""".format(base_name=base_name, name=x.name))

    fh.write("""
};
""")

    # Namespace end
    fh.write("""
}
""")

    fc.write("""
}
""")

def write_packets():
    fh = open("Protocol.h", "w")
    fc = open("Protocol.cpp", "w")

    fh.write("""
/* Automatically generated file */

#include <stdint.h>
#include <string>
#include <vector>
#include "ByteQueue.h"

namespace dakara {
namespace protocol {

namespace clientgm {
    class ClientGMPacket;
}

namespace client {
    class ClientPacketHandler;
}
namespace clientgm {
    class ClientGMPacketHandler;
}
namespace server {
    class ServerPacketHandler;
}

class PacketHandler {
public:
    virtual ~PacketHandler() {};
    virtual client::ClientPacketHandler* getPacketHandlerClientPacket() = 0;
    virtual clientgm::ClientGMPacketHandler* getPacketHandlerClientGMPacket() = 0;
    virtual server::ServerPacketHandler* getPacketHandlerServerPacket() = 0;
};

class Packet {
public:
    explicit Packet(int id) : id_(id) {}
    virtual ~Packet() {}

    int get_id() const { return id_; }

    virtual void serialize(clsByteQueue* buffer) = 0;
    virtual void dispatch(PacketHandler* d) = 0;

protected:
    int id_;
};

""")

    fc.write("""
/* Automatically generated file */

#include "Protocol.h"

namespace dakara {
namespace protocol {

""")

    write_packets_from(fh, fc, "ClientPacket", "client", CLIENT_PACKETS)
    write_packets_from(fh, fc, "ClientGMPacket", "clientgm", CLIENT_GM_PACKETS)
    write_packets_from(fh, fc, "ServerPacket", "server", SERVER_PACKETS)

    fh.write("""
}
}
""")

    fc.write("""
}
}
""")

    fh.close()
    fc.close()

def main():
    write_packets()

if __name__ == '__main__':
    main()
