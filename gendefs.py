

class Packet:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def get_header_fmt(self):
        return """
class {name} : public {base_name} {{
public:
    {name}();
    {name}(clsByteQueue* buffer);

    virtual void serialize(clsByteQueue* buffer) const;
    virtual void dispatch(PacketHandler* d);

{header_fields}
}};

inline {name} Build{name}({header_fields_signature}) {{
    {name} e;
{items_assign_e}
    return e;
}}
"""

    def get_ctor1_fmt(self):
        return """
{name}::{name}() : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
}}
"""

    def get_ctor2_fmt(self):
        return """
{name}::{name}(clsByteQueue* buffer) : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
    buffer->ReadByte(); /* PacketID */
{ctor_fields_bytequeue}
}}
"""

    def get_serialize_fmt(self):
        return """
void {name}::serialize(clsByteQueue* buffer) const {{
    buffer->WriteByte({base_name}ID_{name}); /* PacketID: {packet_id} */
{serialize_fields}
}}
"""

    def get_dispatcher_fmt(self):
        return """
void {name}::dispatch(PacketHandler* d) {{
    d->getPacketHandler{base_name}()->handle{name}(this);
}}
"""

    def get_ctor_fields_bytequeue_fmt(self, is_array):
        if is_array:
            return "    {{ int i; {arg_name}.resize({array_size}); for (i=0; i<{array_size}; ++i) {arg_name}[i] = buffer->{type_reader_name}(); }}\n"
        else:
            return "    {arg_name} = buffer->{type_reader_name}();\n"

    def get_serialize_fields_fmt(self, is_array):
        if is_array:
            return "    {{ int i; for (i=0; i<{array_size}; ++i) buffer->{type_writer_name}({arg_name}[i]); }}\n"
        else:
            return "    buffer->{type_writer_name}({arg_name});\n"

class PacketGMHeader(Packet):
    def __init__(self, name, args):
        Packet.__init__(self, name, args)

    def get_header_fmt(self):
        return """
class {name} : public {base_name} {{
public:
    {name}();
    {name}(clsByteQueue* buffer);
    virtual ~{name}();

    virtual void serialize(clsByteQueue* buffer) const;
    virtual void dispatch(PacketHandler* d);

    std::unique_ptr<dakara::protocol::clientgm::ClientGMPacket> composite;
{header_fields}
}};
"""

    def get_ctor1_fmt(self):
        return """
{name}::{name}() : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
}}
"""

    def get_ctor2_fmt(self):
        return """
{name}::{name}(clsByteQueue* buffer) : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
    buffer->ReadByte(); /* PacketID */
    composite.reset(dakara::protocol::clientgm::ClientGMPacketFactory(buffer));
/* {ctor_fields_bytequeue} */
}}

{name}::~{name}() {{}}
"""

    def get_serialize_fmt(self):
        return """
void {name}::serialize(clsByteQueue* buffer) const {{
    composite->serialize(buffer);
/* {serialize_fields} */
}}
"""

class PacketGMCommand(Packet):
    def __init__(self, name, args):
        Packet.__init__(self, name, args)

    def get_serialize_fmt(self):
        return """
void {name}::serialize(clsByteQueue* buffer) const {{
    buffer->WriteByte(dakara::protocol::client::ClientPacketID_GMCommands);
    buffer->WriteByte({base_name}ID_{name}); /* PacketID: {packet_id} */
{serialize_fields}
}}
"""

class PacketWithCount(Packet):
    def __init__(self, name, args, reader_type):
        Packet.__init__(self, name, args)
        self.reader_type = reader_type

    def get_header_fmt(self):
        return """
class {name} : public {base_name} {{
public:
    {name}();
    {name}(clsByteQueue* buffer);

    virtual void serialize(clsByteQueue* buffer) const;
    virtual void dispatch(PacketHandler* d);

    struct Item {{
{header_fields}
    }};

    std::vector<Item> Items;

    void addItem({header_fields_signature}) {{
        Item e;
{items_assign_e}
        Items.push_back(e);
    }}
}};
"""

    def get_ctor1_fmt(self):
        return """
{name}::{name}() : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
}}
"""

    def get_ctor2_fmt(self):
        return """
{name}::{name}(clsByteQueue* buffer) : {base_name}({base_name}ID_{name} /* {packet_id} */) {{
    buffer->ReadByte(); /* PacketID */
    std::int32_t Count = buffer->__COUNTREADER__();
    {{ std::int32_t i; 
        for (i=0; i<Count; ++i) {{
            Item e;
{ctor_fields_bytequeue}
            Items.push_back(e);
        }}
    }}
}}
""".replace("__COUNTREADER__", TYPE_TO_READER_NAME[self.reader_type])

    def get_serialize_fmt(self):
        return """
void {name}::serialize(clsByteQueue* buffer) const {{
    buffer->WriteByte({base_name}ID_{name}); /* PacketID: {packet_id} */
    std::int32_t Count = static_cast<std::int32_t>(Items.size());
    buffer->__COUNTWRITER__(Count);
    {{ std::int32_t i; 
        for (i=0; i<Count; ++i) {{
            const Item &e = Items[i];
{serialize_fields}
        }}
    }}
}}
""".replace("__COUNTWRITER__", TYPE_TO_WRITER_NAME[self.reader_type])

    def get_ctor_fields_bytequeue_fmt(self, is_array):
        if is_array:
            return "            {{ int i; e.{arg_name}.resize({array_size}); for (i=0; i<{array_size}; ++i) e.{arg_name}[i] = buffer->{type_reader_name}(); }}\n"
        else:
            return "            e.{arg_name} = buffer->{type_reader_name}();\n"

    def get_serialize_fields_fmt(self, is_array):
        if is_array:
            return "            {{ int i; for (i=0; i<{array_size}; ++i) buffer->{type_writer_name}(e.{arg_name}[i]); }}\n"
        else:
            return "            buffer->{type_writer_name}(e.{arg_name});\n"

TYPE_UNICODE_STRING = 0
TYPE_UNICODE_STRING_FIXED = 1
TYPE_BINARY_STRING = 2
TYPE_BINARY_STRING_FIXED = 3
TYPE_I8 = 4
TYPE_I16 = 5
TYPE_I32 = 6
TYPE_SINGLE = 7 # Float
TYPE_DOUBLE = 8 # Double
TYPE_BOOL = 9
TYPE_ARRAY = (1 << 8)

TYPE_TO_STR = {
    TYPE_UNICODE_STRING: 'std::string',
    TYPE_UNICODE_STRING_FIXED: 'std::string',
    TYPE_BINARY_STRING: 'std::string',
    TYPE_BINARY_STRING_FIXED: 'std::string',
    TYPE_I8: 'std::uint8_t',
    TYPE_I16: 'std::int16_t',
    TYPE_I32: 'std::int32_t',
    TYPE_SINGLE: 'float',
    TYPE_DOUBLE: 'double',
    TYPE_BOOL: 'bool',
}

TYPE_TO_SIGNATURE_STR = {
    TYPE_UNICODE_STRING: 'const std::string&',
    TYPE_UNICODE_STRING_FIXED: 'const std::string&',
    TYPE_BINARY_STRING: 'const std::string&',
    TYPE_BINARY_STRING_FIXED: 'const std::string&',
    TYPE_I8: 'std::uint8_t',
    TYPE_I16: 'std::int16_t',
    TYPE_I32: 'std::int32_t',
    TYPE_SINGLE: 'float',
    TYPE_DOUBLE: 'double',
    TYPE_BOOL: 'bool',
}

TYPE_TO_READER_NAME = {
    TYPE_UNICODE_STRING: 'ReadUnicodeString',
    #TYPE_UNICODE_STRING_FIXED: '',
    #TYPE_BINARY_STRING: '',
    #TYPE_BINARY_STRING_FIXED: 'ReadBinaryFixed',
    TYPE_I8: 'ReadByte',
    TYPE_I16: 'ReadInteger',
    TYPE_I32: 'ReadLong',
    TYPE_SINGLE: 'ReadSingle',
    TYPE_DOUBLE: 'ReadDouble',
    TYPE_BOOL: 'ReadBoolean',
}

TYPE_TO_WRITER_NAME = {
    TYPE_UNICODE_STRING: 'WriteUnicodeString',
    #TYPE_UNICODE_STRING_FIXED: '',
    #TYPE_BINARY_STRING: '',
    #TYPE_BINARY_STRING_FIXED: 'ReadBinaryFixed',
    TYPE_I8: 'WriteByte',
    TYPE_I16: 'WriteInteger',
    TYPE_I32: 'WriteLong',
    TYPE_SINGLE: 'WriteSingle',
    TYPE_DOUBLE: 'WriteDouble',
    TYPE_BOOL: 'WriteBoolean',
}

TYPE_SIZE = {
    TYPE_UNICODE_STRING: 2,
    #TYPE_UNICODE_STRING_FIXED: 0,
    TYPE_BINARY_STRING: 2,
    #TYPE_BINARY_STRING_FIXED: 0,
    TYPE_I8: 1,
    TYPE_I16: 2,
    TYPE_I32: 4,
    TYPE_SINGLE: 4,
    TYPE_DOUBLE: 8,
    TYPE_BOOL: 1,
}
