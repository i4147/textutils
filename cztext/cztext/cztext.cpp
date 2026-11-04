#include <Python.h>
#include <stdint.h>

#include <iostream>
using namespace std;

static const unsigned EN_WIDTH=8;

inline unsigned char_length(unsigned char now) {
    if (now<=0x7F) {
        return EN_WIDTH;
    } else if (0xC0<=now and now<=0xFD) {
        return EN_WIDTH*2;
    }
    return 0;
}
inline bool c_len_more_than(const char* text,const unsigned text_length,unsigned min_length){
    unsigned length=0;
    min_length = min_length*2;
    for(unsigned i=0;i<text_length;++i) {
        unsigned char now = text[i];
        if (0xC0<=now and now<=0xFD) {
            length+=2;
            if(length > min_length){
                return true; 
            } 
        }else if(0<=now and now<=0x7F){
            length+=1;
            if(length > min_length){
                return true; 
            } 
        } 
    }
    return false;
}

inline bool c_cn_len_more_than(const char* text,const unsigned text_length,const unsigned min_length){
    unsigned cn_length=0;
    for(unsigned i=0;i<text_length;++i) {
        unsigned char now = text[i];
        if (0xE0<=now and now<=0xEF) {
            ++cn_length;
            if(cn_length > min_length){
                return true; 
            } 
        } 
    }
    return false;
}

inline unsigned c_overflow_ellipsis (const char* text,const unsigned text_length,const unsigned width) {
    static const unsigned etc_width = EN_WIDTH*3;
    unsigned min_width=width-etc_width;

    if (min_width<=0)return 0;

    unsigned now_width=0,pos=0;

    /*
    1.ascii 2.希腊字母 3.汉字 4.平面符号
    #那么如何判断UTF-8字符的长度呢？
    #0x00-0x7F  1字节
    #0xC0-0xDF  2字节
    #0xE0-0xEF  3字节
    #0xF0-0xF7  4字节
    #0xF8-0xFB  5字节
    #0xFC-0xFD  6字节
    */

    while (text_length>pos) {
        unsigned now_len=char_length(text[pos]);
        unsigned after_width=now_width+now_len;
        //cout<<"now_len "<<now_len<<endl;
        //cout<<"after_width "<<after_width<<endl;
        //cout<<"min_width "<<min_width<<endl;
        if (after_width>min_width) {
            //如果剩余文字少于"..."的长度就可以显示他们,而不是显示...

            unsigned pos2 = pos+1;
            while (text_length>pos2 and width>=after_width) {
                after_width+=char_length(text[pos2]);
                ++pos2;
            }
            if (text_length==pos2)return text_length;
            else {
                goto stop;
            }
        }
        ++pos;
        now_width=after_width;
    }
stop:
    return pos;
};
static PyObject* etc = PyString_FromStringAndSize("...",3);
static PyObject * overflow_ellipsis(PyObject *self,PyObject *args) {
    char * input;
    unsigned input_len;
    int len;
    if (!PyArg_ParseTuple(args,"s#i",&input,&input_len,&len)) {
        return NULL;
    }

    unsigned after_len = c_overflow_ellipsis(input,input_len,len);
    PyObject * o = PyString_FromStringAndSize(input,after_len);
    if (after_len!=input_len) {
        PyString_Concat(&o,etc);
    }
    return o;
};

static PyObject * len_more_than(PyObject *self,PyObject *args) {
    char * input;
    unsigned input_len;
    int len;
    if (PyArg_ParseTuple(args,"s#i",&input,&input_len,&len)) {
        if(c_len_more_than(input,input_len,len)){
            Py_RETURN_TRUE;
        }
    }
    
    Py_RETURN_FALSE;
};

static PyObject * cn_len_more_than(PyObject *self,PyObject *args) {
    char * input;
    unsigned input_len;
    int len;
    if (PyArg_ParseTuple(args,"s#i",&input,&input_len,&len)) {
        if(c_cn_len_more_than(input,input_len,len)){
            Py_RETURN_TRUE;
        }
    }
    
    Py_RETURN_FALSE;
};


static PyMethodDef methods[] = {
    {"overflow_ellipsis",(PyCFunction)overflow_ellipsis,METH_VARARGS,NULL},
    {"cn_len_more_than",(PyCFunction)cn_len_more_than,METH_VARARGS,NULL},
    {"len_more_than",(PyCFunction)len_more_than,METH_VARARGS,NULL},
    {NULL,NULL,0,NULL},
};

PyMODINIT_FUNC initcztext() {
    Py_InitModule3("cztext", methods, "Text Utils");
}

