# simple Makefile to build the event reader with libdywMCEvent.so
# Jianglai 05-12-06
ObjSuf        = o
SrcSuf        = C
DllSuf        = so
OutPutOpt     = -o
ROOTLIBS      = $(shell root-config --libs)
ROOTGLIBS     = $(shell root-config --glibs)
ROOTCFLAGS    = $(shell root-config --cflags)


# Work with Linux with egcs
CXX           = g++
CXXFLAGS      = -O2 -Wall -fPIC
LD            = g++
SOFLAGS       = -shared
LIBS          = $(ROOTLIBS) $(ROOTGLIBS)
CXXFLAGS     += $(ROOTCFLAGS) -Iinclude
LIBS         += -lSpectrum

# -------------------------------------------------------------------------------
#  Generic compilation and linking step to make an executable from
#  a single *.cc file
#
%: %.$(SrcSuf)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)
	@echo "$@ done"

clean:
		@rm -f *.o *~  core
