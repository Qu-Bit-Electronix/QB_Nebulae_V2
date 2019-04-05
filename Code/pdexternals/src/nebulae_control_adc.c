/***********************************************************************
 * This header file contains the mcp3208 Spi class definition.
 * Its main purpose is to communicate with the MCP3208 chip using
 * the userspace spidev facility.
 * The class contains four variables:
 * mode        -> defines the SPI mode used. In our case it is SPI_MODE_0.
 * bitsPerWord -> defines the bit width of the data transmitted.
 *        This is normally 8. Experimentation with other values
 *        didn't work for me
 * speed       -> Bus speed or SPI clock frequency. According to
 *                https://projects.drogon.net/understanding-spi-on-the-raspberry-pi/
 *            It can be only 0.5, 1, 2, 4, 8, 16, 32 MHz.
 *                Will use 1MHz for now and test it further.
 * spifd       -> file descriptor for the SPI device
 *
 * edit mxmxmx: adapted for mcp3208 / terminal tedium
 * edit shensley: adapted for qu-bit nebulae 
 *
 * ****************************************************************************/

/***********************************************************************
 * Outline of changes that need to happen for the Nebulae:
 * - EITHER:
 *     - Change pcm/wm8731 adc select to a spi dev select to choose pot/cvs
 *     - Remove select option, and have 14 outputs CVs and Pots.
 * - Add spidev config for both spi devices
 * - Take inversion of the number out of the pot part of the output prep.
 * 
 **********************************************************************/
#include "m_pd.h"
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#ifdef __arm__
    #include <sys/ioctl.h>
    #include <fcntl.h>
    #include <linux/spi/spidev.h>
#endif

#define ADC_POT 1
#define ADC_CV 2

static t_class *nebulae_control_adc_class;

typedef struct _nebulae_control_adc
{
    t_object x_obj;
    t_outlet *x_out_pots[6];
    t_outlet *x_out_cv[8];
    t_outlet *x_out_status;
    unsigned char mode;
    unsigned char bitsPerWord;
    unsigned int speed;
    unsigned int smooth;
    unsigned int smooth_shift;
    unsigned int deadband;
    int spifd_cv;
    int spifd_pot;
    int _version;
    int a2d_pots[8];
    int a2d_cv[8];
} t_nebulae_control_adc;

static t_nebulae_control_adc *nebulae_control_adc_new(t_floatarg version);
static int nebulae_control_adc_write_read(t_nebulae_control_adc *spi, unsigned char *data, int length, int adc_id);
static void nebulae_control_adc_open(t_nebulae_control_adc *spi, t_symbol *version);
static int nebulae_control_adc_close(t_nebulae_control_adc *spi);
static void nebulae_control_adc_free(t_nebulae_control_adc *spi);

/**********************************************************
 * nebulae_control_adc_open() :function is called by the "open" command
 * It is responsible for opening the spidev device
 * and then setting up the spidev interface.
 * member variables are used to configure spidev.
 * They must be set appropriately before calling
 * this function.
 * *********************************************************/
// #TODO: This can be cleaned up to be like half the number of lines.

static void nebulae_control_adc_open(t_nebulae_control_adc *spi, t_symbol *version){


    int statusVal = 0;
    
    if (strlen(version->s_name) == 0) spi->_version = 0x0; // = wm8731 version
    else spi->_version = 0x1; // = pcm5102a version

    #ifdef __arm__
      // we're using CS1 for Pots :
      spi->spifd_pot =  open("/dev/spidev0.1", O_RDWR); 

      if(spi->spifd_pot < 0) {
        statusVal = -1;
        pd_error(spi, "could not open SPI device 1");
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_WR_MODE, &(spi->mode));
      if(statusVal < 0){
        pd_error(spi, "Could not set SPIMode (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_RD_MODE, &(spi->mode));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPIMode (RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_WR_BITS_PER_WORD, &(spi->bitsPerWord));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI bitsPerWord (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_RD_BITS_PER_WORD, &(spi->bitsPerWord));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI bitsPerWord(RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }  
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_WR_MAX_SPEED_HZ, &(spi->speed));    
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI speed (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_pot, SPI_IOC_RD_MAX_SPEED_HZ, &(spi->speed));    
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI speed (RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
      // using CS0 for CVs
      spi->spifd_cv =  open("/dev/spidev0.0", O_RDWR); 

      if(spi->spifd_cv < 0) {
        statusVal = -1;
        pd_error(spi, "could not open SPI device 0");
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_WR_MODE, &(spi->mode));
      if(statusVal < 0){
        pd_error(spi, "Could not set SPIMode (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_RD_MODE, &(spi->mode));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPIMode (RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_WR_BITS_PER_WORD, &(spi->bitsPerWord));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI bitsPerWord (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_RD_BITS_PER_WORD, &(spi->bitsPerWord));
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI bitsPerWord(RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }  
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_WR_MAX_SPEED_HZ, &(spi->speed));    
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI speed (WR)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }
   
      statusVal = ioctl (spi->spifd_cv, SPI_IOC_RD_MAX_SPEED_HZ, &(spi->speed));    
      if(statusVal < 0) {
        pd_error(spi, "Could not set SPI speed (RD)...ioctl fail");
        nebulae_control_adc_close(spi);
        goto spi_output;
      }

   spi_output:
      if (!statusVal) statusVal = 1;
      else statusVal = 0;
      outlet_float(spi->x_out_status, statusVal);  
 #endif
}

/***********************************************************
 * nebulae_control_adc_close(): Responsible for closing the spidev interface.
 * *********************************************************/
 
static int nebulae_control_adc_close(t_nebulae_control_adc *spi){

    int statusVal = -1;
    if (spi->spifd_cv == -1) {
      pd_error(spi, "nebulae_control_adc: device not open");
      return(-1);
    }
    if (spi->spifd_pot == -1) {
      pd_error(spi, "nebulae_control_adc: device not open");
      return(-1);
    }
  #ifdef __arm__ 
    statusVal = close(spi->spifd_cv);
    statusVal = close(spi->spifd_pot);
  #else 
    statusVal = 0x0;
  #endif  
    if(statusVal < 0) {
      pd_error(spi, "nebulae_control_adc: could not close SPI device");
      exit(1);
    }
    outlet_float(spi->x_out_status, 0);
    spi->spifd_cv = -1;
    spi->spifd_pot = -1;
    return(statusVal);
}

/***********************************************************
 * nebulae_control_adc_smooth(): set smoothing
 * *********************************************************/
 
void nebulae_control_adc_smooth(t_nebulae_control_adc *spi, t_floatarg s){

    unsigned int _shift, _smooth = s;

    if (_smooth < 2) {
      _smooth = 1;
      _shift  = 0;
    }
    else if (_smooth < 4) {
      _smooth = 2;
      _shift  = 1;
    }
    else if (_smooth < 8) {
      _smooth = 4;
      _shift  = 2;
    }
    else if (_smooth < 16) {
      _smooth = 8;
      _shift  = 3;
    }
    else {
      _smooth = 16;  
      _shift  = 4; 
    }
   
    spi->smooth = _smooth;
    spi->smooth_shift = _shift;
}

/***********************************************************
 * nebulae_control_adc_deadband(): set deadband
 * *********************************************************/
 
void nebulae_control_adc_deadband(t_nebulae_control_adc *spi, t_floatarg d){

    int _deadband = (int)d;

    if (_deadband < 0)
      _deadband = 0;
    else if (_deadband > 5)
      _deadband = 5; 
   
    spi->deadband = _deadband;
}

/********************************************************************
 * This function frees the object (destructor).
 * ******************************************************************/
static void nebulae_control_adc_free(t_nebulae_control_adc *spi){
    if (spi->spifd_pot == 0 && spi->spifd_cv == 0) {
      nebulae_control_adc_close(spi);
    }
}
 
/********************************************************************
 * This function writes data "data" of length "length" to the spidev
 * device. Data shifted in from the spidev device is saved back into
 * "data".
 * ******************************************************************/
static int nebulae_control_adc_write_read(t_nebulae_control_adc *spi, unsigned char *data, int length, int adc_id){
 
  #ifdef __arm__ 

    struct spi_ioc_transfer spid[length];
    int i = 0;
    int retVal = -1; 

 
  // one spi transfer for each byte
    for (i = 0 ; i < length ; i++){
      
        memset (&spid[i], 0x0, sizeof (spid[i]));
        spid[i].tx_buf        = (unsigned long)(data + i); // transmit from "data"
        spid[i].rx_buf        = (unsigned long)(data + i); // receive into "data"
        spid[i].len           = sizeof(*(data + i));
        spid[i].speed_hz      = spi->speed;
        spid[i].bits_per_word = spi->bitsPerWord;
    }
 
    if (adc_id == ADC_POT) {
        retVal = ioctl(spi->spifd_pot, SPI_IOC_MESSAGE(length), &spid);
    } else if (adc_id == ADC_CV){
        retVal = ioctl(spi->spifd_cv, SPI_IOC_MESSAGE(length), &spid);
    } else {
        retVal = -1;
    }

    if(retVal < 0){
       pd_error(spi, "problem transmitting spi data..ioctl");
    }
  #else // dummy crap
    int retVal = length + spi->speed + sizeof(*(data));
  #endif
    return retVal;
}

/***********************************************************************
 * mcp3208 enabled external that by default interacts with /dev/spidev0.0 device using
 * nebulae_control_adc_MODE_0 (MODE 0) (defined in linux/spi/spidev.h), speed = 1MHz &
 * bitsPerWord=8.
 *
 * *********************************************************************/
 
static void nebulae_control_adc_bang(t_nebulae_control_adc *spi)
{
  #ifdef __arm__ 
    if (spi->spifd_pot == -1 || spi->spifd_cv == -1) {
        pd_error(spi, "device not open: pot - %d | cv - %d", spi->spifd_pot, spi->spifd_cv);
        return;
  }
  #else 
      return;
  #endif

  int a2dVal_pots[8] = {0,0,0,0,0,0,0,0};
  int a2dVal_cvs[8] = {0,0,0,0,0,0,0,0};
  float f_pots[8];
  float f_cvs[8];
  int a2dChannel = 0;
  unsigned char data[3];
  int numChannels = 8;
  int SCALE = 4000; // make nice zeros ...

  unsigned int SMOOTH = spi->smooth;
  unsigned int SMOOTH_SHIFT = spi->smooth_shift;
  int DEADBAND = spi->deadband;

  
  for (unsigned int i = 0; i < SMOOTH; i++) {

      for (a2dChannel = 0; a2dChannel < numChannels; a2dChannel++) {

        data[0]  =  0x06 | ((a2dChannel>>2) & 0x01);
        data[1]  =  a2dChannel<<6;
        data[2]  =  0x00;

        nebulae_control_adc_write_read(spi, data, 3, ADC_CV);
        a2dVal_cvs[a2dChannel] += (((data[1] & 0x0f) << 0x08) | data[2]); 

        data[0]  =  0x06 | ((a2dChannel>>2) & 0x01);
        data[1]  =  a2dChannel<<6;
        data[2]  =  0x00;

        nebulae_control_adc_write_read(spi, data, 3, ADC_POT);
        a2dVal_pots[a2dChannel] += (((data[1] & 0x0f) << 0x08) | data[2]); 
      }
  }

  for (a2dChannel = 0; a2dChannel < numChannels; a2dChannel++) {

      if (DEADBAND) {

        int tmp_cv = SCALE - (a2dVal_cvs[a2dChannel] >> SMOOTH_SHIFT);
        int tmp2_cv = spi->a2d_cv[a2dChannel];
        int tmp_pot = SCALE - (a2dVal_pots[a2dChannel] >> SMOOTH_SHIFT);
        int tmp2_pot = spi->a2d_pots[a2dChannel];

        if ((tmp2_cv - tmp_cv) > DEADBAND || (tmp_cv - tmp2_cv) > DEADBAND)  
          a2dVal_cvs[a2dChannel] = tmp_cv < 0 ? 0 : tmp_cv;
        else 
          a2dVal_cvs[a2dChannel] = tmp2_cv;
        spi->a2d_cv[a2dChannel] = a2dVal_cvs[a2dChannel];

        if ((tmp2_pot - tmp_pot) > DEADBAND || (tmp_pot - tmp2_pot) > DEADBAND)  
          a2dVal_pots[a2dChannel] = tmp_pot < 0 ? 0 : tmp_pot;
        else 
          a2dVal_pots[a2dChannel] = tmp2_pot;
        spi->a2d_pots[a2dChannel] = a2dVal_pots[a2dChannel];
      }
      else {
        int tmp_cv = SCALE - (a2dVal_cvs[a2dChannel] >> SMOOTH_SHIFT);
        int tmp_pot = SCALE - (a2dVal_pots[a2dChannel] >> SMOOTH_SHIFT);
        a2dVal_cvs[a2dChannel] = tmp_cv < 0 ? 0 : tmp_cv;
        a2dVal_pots[a2dChannel] = tmp_pot < 0 ? 0 : tmp_pot;
      }
  }
  for (int i = 0; i < 8; i++) {
    f_pots[i] = 1.0 - ((float)a2dVal_pots[i] / (float)SCALE);
    f_cvs[i] = ((float)a2dVal_cvs[i] / (float)(SCALE/2)) - 1.0;
  }

  // Copy data to outputs
  for (unsigned int i = 0; i < numChannels; i++) {
    //outlet_float(spi->x_out_cv[i], a2dVal_cvs[i]);
    outlet_float(spi->x_out_cv[i], f_cvs[i]);
    if (i < 3) {
      outlet_float(spi->x_out_pots[i], f_pots[i]);
    } else if (i > 4)  {
      outlet_float(spi->x_out_pots[i - 2], f_pots[i]);
    }
  } 
}

/*************************************************
 * init function.
 * ***********************************************/
static t_nebulae_control_adc *nebulae_control_adc_new(t_floatarg version){
    t_nebulae_control_adc *spi = (t_nebulae_control_adc *)pd_new(nebulae_control_adc_class);
		sys_fontwidth(240);
    /*
    spi->x_out1 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out2 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out3 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out4 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out5 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out6 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out7 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out8 = outlet_new(&spi->x_obj, gensym("float"));
    spi->x_out9 = outlet_new(&spi->x_obj, gensym("float"));
    */
    for (unsigned int i = 0; i < 8; i++) {
        spi->x_out_cv[i] = outlet_new(&spi->x_obj, gensym("float"));
    }
    for (unsigned int i = 0; i < 6; i++) {
        spi->x_out_pots[i] = outlet_new(&spi->x_obj, gensym("float"));
    }
    spi->x_out_status = outlet_new(&spi->x_obj, gensym("float"));
    #ifdef __arm__ 
      spi->mode = SPI_MODE_0;
    #else
      spi->mode = 0x0;
    #endif   
    spi->bitsPerWord = 8;
    spi->speed = 4000000;
    spi->spifd_pot = -1;
    spi->spifd_cv = -1;
    spi->_version = version;
    spi->smooth = 1; 
    spi->smooth_shift = 0;
    spi->deadband = 0;
    return(spi);
}


void nebulae_control_adc_setup(void)
{
    nebulae_control_adc_class = class_new(gensym("nebulae_control_adc"), (t_newmethod)nebulae_control_adc_new,
        (t_method)nebulae_control_adc_free, sizeof(t_nebulae_control_adc), 0, A_DEFSYM, 0);

    class_addmethod(nebulae_control_adc_class, (t_method)nebulae_control_adc_open, gensym("open"), 
        A_DEFSYM, 0);
    class_addmethod(nebulae_control_adc_class, (t_method)nebulae_control_adc_close, gensym("close"), 
        0, 0);
    class_addmethod(nebulae_control_adc_class, (t_method)nebulae_control_adc_smooth, gensym("smooth"), 
        A_DEFFLOAT, 0);
    class_addmethod(nebulae_control_adc_class, (t_method)nebulae_control_adc_deadband, gensym("deadband"), 
        A_DEFFLOAT, 0);
    class_addbang(nebulae_control_adc_class, nebulae_control_adc_bang);
}
