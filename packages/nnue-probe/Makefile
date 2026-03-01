# Stockfish, a UCI chess playing engine derived from Glaurung 2.1
# Copyright (C) 2004-2008 Tord Romstad (Glaurung author)
# Copyright (C) 2008-2015 Marco Costalba, Joona Kiiski, Tord Romstad
# Copyright (C) 2015-2016 Marco Costalba, Joona Kiiski, Gary Linscott, Tord Romstad
#
# Stockfish is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Stockfish is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


### ==========================================================================
### Section 1. General Configuration
### ==========================================================================

### Establish the kernel and operating system name
KERNEL = $(shell uname -s)
ifeq ($(KERNEL),Linux)
	OS = $(shell uname -o)
endif

### ==========================================================================
### Section 2. High-level Configuration
### ==========================================================================

### 2.1. General and architecture defaults

optimize = yes
lto = no
debug = no
sanitize = no
# numa = yes
bits = 64
prefetch = no
popcnt = no
pext = no
sse = no
mmx = no
sse2 = no
ssse3 = no
sse41 = no
avx = no
avx2 = no
avx512 = no
vnni = no
neon = no
ARCH = auto
native = no
embed = no
STRIP = strip

### 2.2 Architecture specific

ifeq ($(ARCH),auto)

    native = yes

    ifeq ($(COMP),)
        CXX=g++
    else ifeq ($(COMP),gcc)
        CXX=g++
    else ifeq ($(COMP),mingw)
        CXX=g++
    else ifeq ($(COMP),icpc)
        CXX=icpc
    else ifeq ($(COMP),clang)
        CXX=clang++
    endif

    ifdef COMPCC
        CXX=$(COMPCC)
    endif

    props = $(shell echo | $(CXX) -march=native -E -dM -)

    x86 = no
    ifneq ($(findstring __i386__,$(props)),)
        x86 = yes
    else ifneq ($(findstring __x86_64__,$(props)),)
        x86 = yes
    endif

    ifeq ($(x86),yes)

        ifneq ($(findstring __i386__,$(props)),)
            arch = i386
            bits = 32
        else
            arch = x86_64
            bits = 64
        endif
        ifneq ($(findstring __AVX512__,$(props)),)
            avx512 = yes
        endif
        ifneq ($(findstring __VNNI__,$(props)),)
            vnni = yes
        endif
        ifeq ($(bits),64)
            ifneq ($(findstring __BMI2__,$(props)),)
                # Let's not use pext on Zen 1 and Zen 2
                ifeq ($(findstring __znver1,$(props)),)
                    ifeq ($(findstring __znver2,$(props)),)
                        pext = yes
                    endif
                endif
            endif
        endif
        ifneq ($(findstring __AVX2__,$(props)),)
            avx2 = yes
        endif
        ifneq ($(findstring __AVX__,$(props)),)
            avx = yes
        endif
        ifneq ($(findstring __SSE4_1__,$(props)),)
            sse41 = yes
        endif
        ifneq ($(findstring __POPCNT__,$(props)),)
            popcnt = yes
        endif
        ifneq ($(findstring __SSSE3__,$(props)),)
            ssse3 = yes
        endif
        ifneq ($(findstring __SSE2__,$(props)),)
            sse2 = yes
        endif
        ifneq ($(findstring __SSE__,$(props)),)
            sse = yes
            prefetch = yes
        endif
        ifeq ($(sse2),no)
            ifneq ($(findstring __MMX__,$(props)),)
                mmx = yes
            endif
        endif

    # AUTO DETECT OTHER ARCHITECTURES BELOW

    else ifneq ($(findstring __ppc__,$(props)),)
        ifneq ($(findstring __ppc64__,$(props)),)
            ARCH=ppc-64
        else
            ARCH=ppc-32
        endif
    
    else ifneq ($(findstring __e2k__,$(props)),)
        ARCH=e2k

    else ifneq ($(findstring __aarch64__,$(props)),)
        ifneq ($(findstring __APPLE__,$(props)),)
            ARCH=apple-silicon
        else
            ARCH=armv8
        endif

    else ifneq ($(findstring __arm__,$(props)),)
        ifneq ($(findstring __ARM_NEON__,$(props)),)
            ARCH=armv7-neon
        else
            ARCH=armv7
        endif

    else ifneq ($(findstring __LP64__,$(props)),)
        # this is a fallback for 64-bit architectures that we don't know about, but that support 64-bit instructions
        ARCH=general-64
    else
        ARCH=general-32
    endif
endif



ifneq ($(findstring x86,$(ARCH)),)

    # User specified x86-32/64 architecture, with optional instruction set components
    # Auto-detecting is better, but this allows users to override the auto-detection if needed.

    ifneq ($(findstring x86-32,$(ARCH)),)
        arch = i386
        bits = 32
    else
        arch = x86_64
        sse = yes
        sse2 = yes
    endif

    ifneq ($(findstring -sse,$(ARCH)),)
        sse = yes
    endif

    ifneq ($(findstring -popcnt,$(ARCH)),)
        popcnt = yes
    endif

    ifneq ($(findstring -mmx,$(ARCH)),)
        mmx = yes
    endif

    ifneq ($(findstring -sse2,$(ARCH)),)
        sse = yes
        sse2 = yes
    endif

    ifneq ($(findstring -ssse3,$(ARCH)),)
        sse = yes
        ssse3 = yes
    endif

    ifneq ($(findstring -sse41,$(ARCH)),)
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
    endif

    ifneq ($(findstring -modern,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
    endif

    ifneq ($(findstring -avx,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        avx = yes
    endif

    ifneq ($(findstring -avx2,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        avx2 = yes
    endif

    ifneq ($(findstring -bmi2,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        avx2 = yes
        pext = yes
    endif

    ifneq ($(findstring -avx512,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        avx2 = yes
        pext = yes
        avx512 = yes
    endif

    ifneq ($(findstring -vnni,$(ARCH)),)
        popcnt = yes
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        avx2 = yes
        pext = yes
        vnni = yes
    endif

    ifeq ($(sse),yes)
        prefetch = yes
    endif

    # 64-bit pext is not available on x86-32
    ifeq ($(bits),32)
        pext = no
    endif


else

    # Either auto-detected non-x86 architecture, or user-specified non-x86 architecture

    ifeq ($(ARCH),general-32)
        arch = any
        bits = 32
    endif

    ifeq ($(ARCH),general-64)
        arch = any
    endif

    ifeq ($(ARCH),armv7)
        arch = armv7
        prefetch = yes
        bits = 32
        lto = yes
    endif

    ifeq ($(ARCH),armv7-neon)
        arch = armv7
        prefetch = yes
        popcnt = yes
        neon = yes
        bits = 32
        lto = yes
    endif

    ifeq ($(ARCH),armv8)
        arch = armv8
        prefetch = yes
        popcnt = yes
        neon = yes 
        lto = yes
    endif

    ifeq ($(ARCH),apple-silicon)
        arch = arm64
        prefetch = yes
        popcnt = yes
        neon = yes
        lto = yes
        # numa = no
    endif

    ifeq ($(ARCH),ppc-32)
        arch = ppc
        bits = 32
    endif

    ifeq ($(ARCH),ppc-64)
        arch = ppc64
        popcnt = yes
        prefetch = yes
    endif

    ifneq ($(findstring e2k,$(ARCH)),)
        arch = e2k
        bits = 64
        sse = yes
        sse2 = yes
        ssse3 = yes
        sse41 = yes
        popcnt = yes
    endif

endif


### ==========================================================================
### Section 3. Low-level configuration
### ==========================================================================

### 3.1 Selecting compiler (default = gcc)

CFLAGS += -Wall -std=c++11 $(EXTRACFLAGS)
DEPENDFLAGS += -std=c++11
LDFLAGS += $(EXTRALDFLAGS) -lm

ifeq ($(COMP),)
	COMP=gcc
endif

ifeq ($(COMP),gcc)
	comp=gcc
	CXX=g++
	CFLAGS += -pedantic -Wextra -Wshadow
	ifeq ($(ARCH),$(filter $(ARCH),armv7 armv8))
		ifeq ($(OS),Android)
			CFLAGS += -m$(bits)
			LDFLAGS += -m$(bits)
		endif
	else
		CFLAGS += -m$(bits)
		LDFLAGS += -m$(bits)
	endif

	ifeq ($(arch),$(filter $(arch),armv7))
		LDFLAGS += -latomic
	endif

	ifneq ($(KERNEL),Darwin)
		LDFLAGS += -Wl,--no-as-needed
	endif

	ifneq ($(KERNEL),$(filter $(KERNEL),Linux Darwin Haiku))
		CFLAGS += -Wno-pedantic-ms-format
	endif
endif

ifeq ($(COMP),mingw)
	comp=mingw
	CFLAGS += -pedantic -Wextra -Wshadow -Wno-pedantic-ms-format -m$(bits)
	LDFLAGS += -m$(bits)
	ifeq ($(KERNEL),Linux)
		ifeq ($(bits),64)
			ifeq ($(shell which x86_64-w64-mingw32-cc-posix),)
				CXX=x86_64-w64-mingw32-g++
			else
				CXX=x86_64-w64-mingw32-cc-posix
			endif
		else
			ifeq ($(shell which i686-w64-mingw32-cc-posix),)
				CXX=i686-w64-mingw32-g++
			else
				CXX=i686-w64-mingw32-cc-posix
			endif
		endif
	else
		CXX=g++
	endif
endif

ifeq ($(COMP),icpc)
	comp=icpc
	CXX=icpc
	CFLAGS += -diag-disable 344,711,2259,2330 -Wcheck -Wabi -Wdeprecated -strict-ansi
endif

ifeq ($(COMP),clang)
	comp=clang
	CXX=clang++
	CFLAGS += -pedantic -Wextra -Wshadow

	ifneq ($(KERNEL),Darwin)
	ifneq ($(KERNEL),OpenBSD)
	ifneq ($(KERNEL),FreeBSD)
		LDFLAGS += -latomic
	endif
	endif
	endif

	ifeq ($(arch),$(filter $(arch),armv7 armv8))
		ifeq ($(OS),Android)
			CFLAGS += -m$(bits)
			LDFLAGS += -m$(bits)
		endif
	else
		CFLAGS += -m$(bits)
		LDFLAGS += -m$(bits)
	endif
endif

ifneq ($(COMP),mingw)
ifeq ($(KERNEL),$(filter $(KERNEL),Linux Darwin Haiku))
	CFLAGS += -D_DEFAULT_SOURCE -D_BSD_SOURCE
endif
endif

ifeq ($(KERNEL),Darwin)
	CFLAGS += -arch $(arch) -mmacosx-version-min=10.14
	LDFLAGS += -arch $(arch) -mmacosx-version-min=10.14
    STRIP += -x
	XCRUN = xcrun
endif

# To cross-compile for Android, NDK version r21 or later is recommended.
# In earlier NDK versions, you'll need to pass -fno-addrsig if using GNU
# binutils. Currently we don't know how to make PGO builds with the NDK yet.
ifeq ($(COMP),ndk)
	CFLAGS += -fPIE
	comp=clang
	ifeq ($(arch),armv7)
		CXX=armv7a-linux-androideabi16-clang++
		CFLAGS += -mthumb -march=armv7-a -mfloat-abi=softfp -mfpu=neon
		STRIP=arm-linux-androideabi-strip
	endif
	ifeq ($(arch),armv8)
		CXX=aarch64-linux-android21-clang++
		STRIP=aarch64-linux-android-strip
	endif
	LDFLAGS += -static -latomic -z muldefs
endif

### Allow overwriting CC from command line
ifdef COMPCC
	CXX=$(COMPCC)
endif

### On mingw use Windows threads, otherwise POSIX
ifneq ($(comp),mingw)
	# On Android Bionic's C library comes with its own pthread implementation bundled in
	ifneq ($(OS),Android)
		# Haiku has pthreads in its libroot, so only link it in on other platforms
		ifneq ($(KERNEL),Haiku)
			ifneq ($(COMP),ndk)
				LDFLAGS += -lpthread
			endif
		endif
	endif
endif

### 3.2 Debugging
ifeq ($(debug),no)
	CFLAGS += -DNDEBUG
else
	CFLAGS += -g
endif

ifneq ($(sanitize),no)
	CFLAGS += -g3 -fsanitize=$(sanitize)
	LDFLAGS += -fsanitize=$(sanitize)
endif

### 3.3 Optimization
ifeq ($(optimize),yes)

	CFLAGS += -O3

	ifeq ($(comp),$(filter $(comp),gcc mingw))
		ifeq ($(extra),yes)
			CFLAGS += -fira-loop-pressure -fconserve-stack -fmodulo-sched -fmodulo-sched-allow-regmoves -fsched-pressure -flimit-function-alignment -fno-tree-pre
		endif

		ifeq ($(OS),Android)
			CFLAGS += -fno-gcse -mthumb -march=armv7-a -mfloat-abi=softfp
		endif
	endif

	ifeq ($(comp),$(filter $(comp),gcc clang icpc))
		ifeq ($(KERNEL),Darwin)
			CFLAGS += -mdynamic-no-pic
		endif
	endif

	ifeq ($(comp),clang)
		CFLAGS += -fexperimental-new-pass-manager
	endif
endif

### 3.4 Bits
ifeq ($(bits),64)
	CFLAGS += -DIS_64BIT
endif

### 3.5 prefetch and sse
ifeq ($(prefetch),no)
	CFLAGS += -DNO_PREFETCH
endif

### 3.6 popcnt
ifeq ($(popcnt),yes)
	ifeq ($(arch),$(filter $(arch),ppc64 armv7 armv8 arm64))
		CFLAGS += -DUSE_POPCNT
	else
	ifeq ($(comp),icpc)
		CFLAGS += -msse3 -DUSE_POPCNT
	else
		CFLAGS += -msse3 -mpopcnt -DUSE_POPCNT
	endif
	endif
endif

### 3.7 pext
ifeq ($(pext),yes)
	CFLAGS += -DUSE_PEXT
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -msse4 -mbmi2
	endif
endif

### 3.8 vector instructions
ifeq ($(avx2),yes)
	CFLAGS += -DUSE_AVX2
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mavx2
	endif
else ifeq ($(avx),yes)
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mavx
	endif
endif

ifeq ($(avx512),yes)
	CFLAGS += -DUSE_AVX512
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mavx512f -mavx512bw
	endif
endif

ifeq ($(vnni),yes)
	CFLAGS += -DUSE_VNNI
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mavx512f -mavx512bw -mavx512vnni -mavx512dq -mavx512vl
	endif
endif

ifeq ($(sse41),yes)
	CFLAGS += -DUSE_SSE41
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -msse4.1
	endif
endif

ifeq ($(ssse3),yes)
	CFLAGS += -DUSE_SSSE3
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mssse3
	endif
endif

ifeq ($(sse2),yes)
	CFLAGS += -DUSE_SSE2
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -msse2
	endif
endif

ifeq ($(sse),yes)
	CFLAGS += -msse -DUSE_SSE
endif

ifeq ($(mmx),yes)
	CFLAGS += -DUSE_MMX
	ifeq ($(comp),$(filter $(comp),gcc clang mingw))
		CFLAGS += -mmmx
	endif
endif

ifeq ($(neon),yes)
	CFLAGS += -DUSE_NEON
	ifeq ($(KERNEL),Linux)
	ifneq ($(COMP),ndk)
	ifneq ($(arch),armv8)
		CFLAGS += -mfpu=neon
	endif
	endif
	endif
endif

ifeq ($(native),yes)
	ifneq ($(findstring ppc,$(arch)),)
		CFLAGS += -mcpu=native -mtune=native
	else ifneq ($(findstring arm,$(arch)),)
		CFLAGS += -march=native -mtune=native
	else
		CFLAGS += -march=native
	endif
endif

# Not used in C++ versions...
### numa
# ifeq ($(numa),yes)
# 	CFLAGS += -DNUMA
#         ifeq ($(KERNEL),Linux)
#         ifneq ($(comp),mingw)
# 		LDFLAGS += -lnuma
#         endif
#         endif
# endif

### 3.9 Link Time Optimization
### This is a mix of compile and link time options because the lto link phase
### needs access to the optimization flags.
ifeq ($(lto),yes)
ifeq ($(optimize),yes)
ifeq ($(debug),no)
	ifeq ($(comp),clang)
		CFLAGS += -flto
		ifneq ($(findstring MINGW,$(KERNEL)),)
			CFLAGS += -fuse-ld=lld
		else ifneq ($(findstring MSYS,$(KERNEL)),)
			CFLAGS += -fuse-ld=lld
		endif
		LDFLAGS += $(CFLAGS)

# GCC and CLANG  user different methods for parallelizing LTO, and CLANG
# pretends to be GCC on some systems.
	else ifeq ($(comp),gcc)
	ifeq ($(gccisclang),)
		CFLAGS += -flto
		LDFLAGS += $(CFLAGS) -flto=jobserver
		ifneq ($(findstring MINGW,$(KERNEL)),)
			LDFLAGS += -save-temps
		else ifneq ($(findstring MSYS,$(KERNEL)),)
			LDFLAGS += -save-temps
		endif
	else
		CFLAGS += -flto
		LDFLAGS += $(CFLAGS)
	endif

# To use LTO and static linking on windows, the tool chain requires a recent
# gcc: gcc version 10.1 in msys2 or TDM-GCC version 9.2 are known to work,
# older might not.
	else ifeq ($(comp),mingw)
		CFLAGS += -flto
		LDFLAGS += $(CFLAGS) -flto=jobserver
	endif
endif
endif
endif

### 3.9 Android 5 can only run position independent executables. Note that this
### breaks Android 4.0 and earlier.
ifeq ($(arch),armv7)
	CFLAGS += -fPIE
	LDFLAGS += -fPIE
endif




### ==========================================================================
### Section 4. Public targets
### ==========================================================================

EXE = nnue_probe/libnnueprobe.so
RM = rm -rf
OBJ = src/misc.o src/nnue.o
HPP = src/misc.h src/nnue.h

NNUENET = $(shell grep DefaultEvalFile src/nnue.h | sed 's/.*\(nn-[a-z0-9]\{12\}.nnue\).*/\1/')
NNUENET_PATH = nnue_probe/$(NNUENET)

default:
	$(MAKE) $(EXE) strip

clean:
	$(RM) $(OBJ) $(EXE) core.* cluster.* *.gcda $(NNUENET_PATH)

strip:
	$(STRIP) $(EXE)

##############
# Dependencies
############## 

$(EXE): net $(OBJ)
	$(CXX) -o $@ $(OBJ) $(LDFLAGS) -shared 

%.o: %.cpp $(HPP)
	$(CXX) $(CFLAGS) -c -fPIC -o $@ $<

net:
	@echo "Default net: $(NNUENET)"
	$(eval nnuedownloadurl := https://tests.stockfishchess.org/api/nn/$(NNUENET))
	$(eval curl_or_wget := $(shell if hash curl 2>/dev/null; then echo "curl -skL"; elif hash wget 2>/dev/null; then echo "wget -qO-"; fi))
	@mkdir -p $(dir $(NNUENET_PATH))
	@if test -f "$(NNUENET_PATH)"; then echo "Already available."; else echo "Downloading $(nnuedownloadurl)"; $(curl_or_wget) $(nnuedownloadurl) > $(NNUENET_PATH); fi
	$(eval shasum_command := $(shell if hash shasum 2>/dev/null; then echo "shasum -a 256 "; elif hash sha256sum 2>/dev/null; then echo "sha256sum "; fi))
	@if [ "$(NNUENET)" != "nn-"`$(shasum_command) $(NNUENET_PATH) | cut -c1-12`".nnue" ]; then echo "Failed download or $(NNUENET_PATH) corrupted, please delete!"; exit 1; fi

help:
	@echo ""
	@echo "To compile PROBE-NNUE, type: "
	@echo ""
	@echo "make [ARCH=arch] [COMP=compiler]"
	@echo ""
	@echo "Supported archs:"
	@echo ""
	@echo "auto                    > Auto-detect optimal architecture (default)"
	@echo "x86-64-avx512-vnni      > x86 64-bit with 512-bit AVX512/VNNI support"
	@echo "x86-64-avx512           > x86 64-bit with 512-bit AVX512 support"
	@echo "x86-64-vnni             > x86 64-bit with 256-bit AVX2/VNNI support"
	@echo "x86-64-bmi2             > x86 64-bit with AVX2 and BMI2 support"
	@echo "x86-64-avx2             > x86 64-bit with 256-bit AVX2 support"
	@echo "x86-64-avx              > x86 64-bit with AVX support (VEX encoding)"
	@echo "x86-64-sse41-popcnt     > x86 64-bit with SSE4.1 and popcount support"
	@echo "x86-64-modern           > common modern CPU, currently x86-64-sse41-popcnt"
	@echo "x86-64-ssse3            > x86 64-bit with SSSE3 support"
	@echo "x86-64-sse3-popcnt      > x86 64-bit with SSE3 and popcount support"
	@echo "x86-64                  > x86 64-bit generic (with SSE2 support)"
	@echo "x86-32-avx512-vnni      |"
	@echo "x86-32-...              | same as for x86-64"
	@echo "x86-32-sse3-popcnt      |"
	@echo "x86-32-sse2             > x86 32-bit with SSE2 support"
	@echo "x86-32-mmx-sse          > x86 32-bit with MMX and SSE support"
	@echo "x86-32-mmx              > x86 32-bit with MMX support"
	@echo "x86-32                  > x86 32-bit generic"
	@echo "ppc-64                  > PPC 64-bit"
	@echo "ppc-32                  > PPC 32-bit"
	@echo "armv8                   > ARMv8 64-bit with popcnt and neon"
	@echo "armv7-neon              > ARMv7 32-bit with popcnt and neon"
	@echo "armv7                   > ARMv7 32-bit"
	@echo "apple-silicon           > Apple silicon ARM64"
	@echo "e2k                     > Elbrus 2000"
	@echo "general-64              > unspecified 64-bit"
	@echo "general-32              > unspecified 32-bit"
	@echo ""
	@echo "When using many threads, 256-bit AVX2 may perform better than 512-bit AVX512."
	@echo ""
	@echo "Supported compilers:"
	@echo ""
	@echo "gcc                     > Gnu compiler (default)"
	@echo "mingw                   > Gnu compiler with MinGW under Windows"
	@echo "clang                   > LLVM Clang compiler"
	@echo "icpc                    > Intel compiler"
