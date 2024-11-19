pkgconfigdir = $(libdir)/pkgconfig

AM_CFLAGS = -Wall -g \
        -Wundef \
        -Wstrict-prototypes \
        -Wno-trigraphs \
        $(SECUREMSM-NOSHIP_CFLAGS) \
        -I$(top_srcdir)/../smcinvoke/inc \
        -I$(top_srcdir)/../mink/inc/interface \
        -I$(top_srcdir)/../QSEEComAPI/ \
        -I$(top_srcdir)/../tzcommon/inc

ACLOCAL_AMFLAGS = -I m4

AM_CPPFLAGS = -D__packed__= \
    -DFEATURE_LE_DIAG \
    -DOE \
    $(SECUREMSMNOSHIP_CFLAGS)

bin_PROGRAMS = uefi_sec

uefi_sec_SOURCES = uefi_sec.c SecureUILib.h
uefi_sec_CPPFLAGS = $(AM_CPPFLAGS)
uefi_sec_CFLAGS = $(AM_CFLAGS)
uefi_sec_LDFLAGS = -lpthread -ldl -lQseeComApi -ldrmfs -lrpmb -lssd
uefi_sec_LDADD = -lQseeComApi -ldmabufheap -lqcbor
uefi_sec_LDADD += -lminkdescriptor
