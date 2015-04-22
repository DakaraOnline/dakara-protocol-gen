
class Packet {
public:
    explicit Packet(int id) : id_(id) {}
    virtual ~Packet() {}

    int get_id() const { return id_; }

    virtual void serialize(clsByteQueue* buffer) = 0;

protected:
    int id_;
};

class ClientPacket : public Packet {
public:
    explicit ClientPacket(int id) : Packet(id) {}
};

ClientPacket* ClientPacketFactory(clsByteQueue* buffer);

class LoginExistingChar : public ClientPacket {
public:
    LoginExistingChar();

    virtual void serialize(clsByteQueue* buffer);

    static LoginExistingChar* factory(clsByteQueue* buffer);

    std::string UserName;
    std::string Password;
    std::uint8_t VerA;
    std::uint8_t VerB;
    std::uint8_t VerC;
};

/*********************** CPP ************************/

ClientPacket* ClientPacketFactory(clsByteQueue* buffer) {
    if (buffer->length() < 1) return 0;
    ClientPacket *p = 0;
    int PacketID = buffer->PeekByte();

    switch (PacketID) {
        case 0:
            p = LoginExistingChar::factory(buffer);
            break;

    }
    return p;
}

LoginExistingChar::LoginExistingChar() : ClientPacket(0) {
    VerA = 0;
    VerB = 0;
    VerB = 0;
}

LoginExistingChar* LoginExistingChar::factory(clsByteQueue* buffer) {
    if (buffer->length() < 7) return 0;
    LoginExistingChar *p = 0;

    try {
        p = new LoginExistingChar();
        p->UserName = buffer->ReadUnicodeString();
        p->Password = buffer->ReadUnicodeString();
        p->VerA = buffer->ReadByte();
        p->VerB = buffer->ReadByte();
        p->VerC = buffer->ReadByte();
    } catch (...) {
        if (p) delete p;
        throw;
    }
    return p;
}

void LoginExistingChar::serialize(clsByteQueue* buffer) {
    buffer->WriteByte(get_id());
    buffer->WriteUnicodeString(UserName);
    buffer->WriteUnicodeString(Password);
    buffer->WriteByte(VerA);
    buffer->WriteByte(VerB);
    buffer->WriteByte(VerC);
}
