#pragma once

#include <G3Frame.h>
#include <G3Map.h>

#include <stdint.h>

using namespace std;

/* Simple class for basic boost-python example. */

class TestClass {
public:
    void runme();
};


/* G3-serializable example. */

class TestFrame : public G3FrameObject {
public:
    int32_t session_id;
    string data_source;
    
    string Description() const;
    string Summary() const;
    template <class A> void serialize(A &ar, unsigned v);
};

G3_SERIALIZABLE(TestFrame, 0);
