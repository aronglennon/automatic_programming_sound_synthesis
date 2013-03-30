//	ipoke~ - a buffer writter with skipped address filling feature (interpolated or not)
//	by Pierre Alexandre Tremblay
//	v.2 optimised at the University of Huddersfield, with the help of the dev@cycling74.com comments of Mark Pauley, Alex Harker, Ben Neville and Peter Castine, addressed  to me or to others.
//	v.3 updated for Max5
//	v.4 added overdub ratio and Max6 support

#include "ext.h"
#include "ext_obex.h"
#include "ext_common.h" // contains CLIP macro
#include "z_dsp.h"
#include "buffer.h"	// this defines our buffer's data structure and other goodies

void *ipoke_class;

typedef struct _ipoke
{
    t_pxobject l_obj;
    t_symbol *l_sym;
    t_buffer *l_buf;
    short l_chan;
	Boolean l_interp;
	double l_overdub;
	long l_index_precedent;
	long l_nb_val;
	double l_valeur;
} t_ipoke;

void *ipoke_new(t_symbol *s, long chan);

void ipoke_dsp(t_ipoke *x, t_signal **sp);
void ipoke_dsp64(t_ipoke *x, t_object *dsp64, short *count, double samplerate, long maxvectorsize, long flags);

t_int *ipoke_perform(t_int *w);
void ipoke_perform64(t_ipoke *x, t_object *dsp64, double **ins, long numins, double **outs, long numouts, long vec_size, long flags, void *userparam);

void ipoke_set(t_ipoke *x, t_symbol *s);
void ipoke_int(t_ipoke *x, long n);
void ipoke_interp(t_ipoke *x, long n);
void ipoke_overdub(t_ipoke *x, double n);
void ipoke_dblclick(t_ipoke *x);
void ipoke_assist(t_ipoke *x, void *b, long m, long a, char *s);

inline long wrap_index(size_t index, size_t arrayLength);

t_symbol *ps_buffer;

void main(void)
{
	t_class *c;

	c = class_new("ipoke~", (method)ipoke_new, (method)dsp_free, (short)sizeof(t_ipoke), 0L, A_SYM, A_DEFLONG, 0);
	class_addmethod(c, (method)ipoke_int, "int", A_LONG, 0);
	class_addmethod(c, (method)ipoke_dsp, "dsp", A_CANT, 0);
	class_addmethod (c, (method)ipoke_dsp64, "dsp64", A_CANT, 0L); //support max6 64 bits
	class_addmethod(c, (method)ipoke_set, "set", A_SYM, 0);
	class_addmethod(c, (method)ipoke_interp, "interp", A_LONG, 0);
	class_addmethod(c, (method)ipoke_overdub, "overdub", A_FLOAT, 0);
	class_addmethod(c, (method)ipoke_assist, "assist", A_CANT, 0);
	class_addmethod(c, (method)ipoke_dblclick, "dblclick", A_CANT, 0);
	class_dspinit(c);
	class_register(CLASS_BOX, c);
	ipoke_class = c;
	
	ps_buffer = gensym("buffer~");

//	post("ipoke4.99");
	
	return 0;
	}


void *ipoke_new(t_symbol *s, long chan)
{
	t_ipoke *x = object_alloc(ipoke_class);
	
	dsp_setup((t_pxobject *)x, 3);

	x->l_sym = s;
	x->l_interp = 1;
	x->l_overdub = 0;
	x->l_index_precedent = -1;
	
	if (chan)
		x->l_chan = CLIP(chan,1,4) - 1;		// check the argument - initial buffer channel

	return (x);
}

void ipoke_dsp(t_ipoke *x, t_signal **sp)
{
    ipoke_set(x,x->l_sym);
	x->l_index_precedent = -1;
    dsp_add(ipoke_perform, 4, x, sp[0]->s_vec, sp[1]->s_vec, sp[0]->s_n);
//	post("dsp32");
}

void ipoke_dsp64(t_ipoke *x, t_object *dsp64, short *count, double samplerate, long maxvectorsize, long flags)
{	
    ipoke_set(x,x->l_sym);
	x->l_index_precedent = -1;
	object_method(dsp64, gensym("dsp_add64"), x, ipoke_perform64, 0, NULL);
//	post("dsp64");
}

t_int *ipoke_perform(t_int *w)
{
    t_ipoke *x = (t_ipoke *)(w[1]);
    float *inval = (float *)(w[2]);
    float *inind = (float *)(w[3]);
	int n = (int)(w[4]);
	
	t_buffer *b = x->l_buf;
	
	Boolean interp, dirty_flag;
	short chan, nc;
	float *tab;
	double valeur_entree, valeur, index_tampon, coeff, overdub;
	long frames, nb_val, index, index_precedent, pas, i,demivie;
	
	if (!b || x->l_obj.z_disabled)
		goto out;
	ATOMIC_INCREMENT(&b->b_inuse);
	if (!b->b_valid) {
		ATOMIC_DECREMENT(&b->b_inuse);
		goto out;
	}
	
	tab = b->b_samples;
	chan = x->l_chan;
	nc = b->b_nchans;
	frames = b->b_frames;
	demivie = (long)(frames * 0.5);

	index_precedent = x->l_index_precedent;
	valeur = x->l_valeur;
	nb_val = x->l_nb_val;
	interp = x->l_interp;
	dirty_flag = false;
	overdub = x->l_overdub;
	
	if (overdub != 0.)
	{
		if (interp)
		{
			while (n--)	// dsp loop with interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
						
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + (valeur/nb_val);		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);		// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + valeur;				// write the average value at the last index
						dirty_flag = true;

						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								pas -= frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient

								for(i=(index_precedent-1);i>=0;i--)					// fill the gap to zero
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
								for(i=(frames-1);i>index;i--)						// fill the gap from the top
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent+1); i<index; i++)
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								pas += frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient

								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
								for(i=0;i<index;i++)							// fill the gap from zero
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent-1); i>index; i--)
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}							
							}
						}

						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
		else
		{
			while (n--)	// dsp loop without interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
						
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + (valeur/nb_val);		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);			// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
										
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								for(i=(index_precedent-1);i>=0;i--)				// fill the gap to zero
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								for(i=(frames-1);i>index;i--)					// fill the gap from the top
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent+1); i<index; i++)
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								for(i=0;i<index;i++)							// fill the gap from zero
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent-1); i>index; i--)
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
						}

						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
	}
	else
	{
		if (interp)
		{
			while (n--)	// dsp loop with interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
						
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = valeur/nb_val;		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);		// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = valeur;				// write the average value at the last index
						dirty_flag = true;

						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								pas -= frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient

								for(i=(index_precedent-1);i>=0;i--)					// fill the gap to zero
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}
								for(i=(frames-1);i>index;i--)						// fill the gap from the top
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent+1); i<index; i++)
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								pas += frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient

								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
								for(i=0;i<index;i++)							// fill the gap from zero
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent-1); i>index; i--)
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}							
							}
						}

						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
		else
		{
			while (n--)	// dsp loop without interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
						
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = valeur/nb_val;		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);			// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
										
						tab[index_precedent * nc + chan] = valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								for(i=(index_precedent-1);i>=0;i--)				// fill the gap to zero
									tab[i * nc + chan] = valeur;
								for(i=(frames-1);i>index;i--)					// fill the gap from the top
									tab[i * nc + chan] = valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent+1); i<index; i++)
									tab[i * nc + chan] = valeur;
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
									tab[i * nc + chan] = valeur;
								for(i=0;i<index;i++)							// fill the gap from zero
									tab[i * nc + chan] = valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent-1); i>index; i--)
									tab[i * nc + chan] = valeur;
							}
						}

						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
	}
	//update the mod time
	if (dirty_flag)
		object_method((t_object *)b, gensym("dirty"));
		
	//mark the buffers as free
	ATOMIC_DECREMENT(&b->b_inuse);

	x->l_index_precedent = index_precedent;
	x->l_valeur = valeur;
	x->l_nb_val = nb_val;

out:
	return (w + 5);
}

void ipoke_perform64(t_ipoke *x, t_object *dsp64, double **ins, long numins, double **outs, long numouts, long vec_size, long flags, void *userparam)
{
    //this is the only different code to above//
    double *inval = ins[0];
    double *inind = ins[1];
	long n = vec_size;
	//below is the same

	t_buffer *b = x->l_buf;
	
	Boolean interp, dirty_flag;
	short chan, nc;
	float *tab;
	double valeur_entree, valeur, index_tampon, coeff, overdub;
	long frames, nb_val, index, index_precedent, pas, i,demivie;
	
	if (!b || x->l_obj.z_disabled)
		goto out;
	ATOMIC_INCREMENT(&b->b_inuse);
	if (!b->b_valid) {
		ATOMIC_DECREMENT(&b->b_inuse);
		goto out;
	}
	
	tab = b->b_samples;
	chan = x->l_chan;
	nc = b->b_nchans;
	frames = b->b_frames;
	demivie = (long)(frames * 0.5);
	
	index_precedent = x->l_index_precedent;
	valeur = x->l_valeur;
	nb_val = x->l_nb_val;
	interp = x->l_interp;
	dirty_flag = false;
	overdub = x->l_overdub;
	
	if (overdub != 0.)
	{
		if (interp)
		{
			while (n--)	// dsp loop with interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
				
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + (valeur/nb_val);		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);		// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								pas -= frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								
								for(i=(index_precedent-1);i>=0;i--)					// fill the gap to zero
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
								for(i=(frames-1);i>index;i--)						// fill the gap from the top
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent+1); i<index; i++)
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								pas += frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
								for(i=0;i<index;i++)							// fill the gap from zero
								{
									valeur += coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent-1); i>index; i--)
								{
									valeur -= coeff;
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								}							
							}
						}
						
						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
		else
		{
			while (n--)	// dsp loop without interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
				
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + (valeur/nb_val);		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);			// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = (tab[index_precedent * nc + chan] * overdub) + valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								for(i=(index_precedent-1);i>=0;i--)				// fill the gap to zero
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								for(i=(frames-1);i>index;i--)					// fill the gap from the top
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent+1); i<index; i++)
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
								for(i=0;i<index;i++)							// fill the gap from zero
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent-1); i>index; i--)
									tab[i * nc + chan] = (tab[i * nc + chan] * overdub) + valeur;
							}
						}
						
						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
	}
	else
	{
		if (interp)
		{
			while (n--)	// dsp loop with interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
				
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = valeur/nb_val;		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);		// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								pas -= frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								
								for(i=(index_precedent-1);i>=0;i--)					// fill the gap to zero
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}
								for(i=(frames-1);i>index;i--)						// fill the gap from the top
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent+1); i<index; i++)
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								pas += frames;									// calculate the new number of steps
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
								for(i=0;i<index;i++)							// fill the gap from zero
								{
									valeur += coeff;
									tab[i * nc + chan] = valeur;
								}
							}
							else												// if not, just fill the gaps
							{
								coeff = (valeur_entree - valeur) / pas;			// calculate the interpolation coefficient
								for (i=(index_precedent-1); i>index; i--)
								{
									valeur -= coeff;
									tab[i * nc + chan] = valeur;
								}							
							}
						}
						
						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
		else
		{
			while (n--)	// dsp loop without interpolation
			{
				valeur_entree = *inval++;
				index_tampon = *inind++;
				
				if (index_tampon < 0.0)											// if the writing is stopped
				{
					if (index_precedent >= 0)									// and if it is the 1st one to be stopped
					{
						tab[index_precedent * nc + chan] = valeur/nb_val;		// write the average value at the last given index
						valeur = 0.0;
						index_precedent = -1;
						dirty_flag = true;
					}
				}			
				else
				{
					index = wrap_index((long)(index_tampon + 0.5),frames);			// round the next index and make sure he is in the buffer's boundaries
					
					if (index_precedent < 0)									// if it is the first index to write, resets the averaging and the values
					{
						index_precedent = index;
						nb_val = 0;
					}
					
					if (index == index_precedent)								// if the index has not moved, accumulate the value to average later.
					{
						valeur += valeur_entree;
						nb_val += 1;
					}
					else														// if it moves
					{
						if (nb_val != 1)										// is there more than one values to average
						{
							valeur = valeur/nb_val;								// if yes, calculate the average
							nb_val = 1;
						}
						
						tab[index_precedent * nc + chan] = valeur;				// write the average value at the last index
						dirty_flag = true;
						
						pas = index - index_precedent;							// calculate the step to do
						
						if (pas > 0)											// are we going up
						{
							if (pas > demivie)									// is it faster to go the other way round?
							{
								for(i=(index_precedent-1);i>=0;i--)				// fill the gap to zero
									tab[i * nc + chan] = valeur;
								for(i=(frames-1);i>index;i--)					// fill the gap from the top
									tab[i * nc + chan] = valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent+1); i<index; i++)
									tab[i * nc + chan] = valeur;
							}
						}
						else													// if we are going down
						{
							if ((-pas) > demivie)								// is it faster to go the other way round?
							{
								for(i=(index_precedent+1);i<frames;i++)			// fill the gap to the top
									tab[i * nc + chan] = valeur;
								for(i=0;i<index;i++)							// fill the gap from zero
									tab[i * nc + chan] = valeur;
							}
							else												// if not, just fill the gaps
							{
								for (i=(index_precedent-1); i>index; i--)
									tab[i * nc + chan] = valeur;
							}
						}
						
						valeur = valeur_entree;									// transfer the new previous value
					}
				}	
				index_precedent = index;										// transfer the new previous address
			}
		}
	}
	//update the mod time
	if (dirty_flag)
		object_method((t_object *)b, gensym("dirty"));
	
	//mark the buffers as free
	ATOMIC_DECREMENT(&b->b_inuse);
	
	x->l_index_precedent = index_precedent;
	x->l_valeur = valeur;
	x->l_nb_val = nb_val;
	
out:
	return;
}

void ipoke_set(t_ipoke *x, t_symbol *s)
{
	t_buffer *b;
	
	b = (t_buffer *)(s->s_thing);
	
	x->l_sym = s;
	if ((b) && (ob_sym(b) == ps_buffer)) {
		x->l_buf = b;
	} else {
		object_error((t_object *)x, "%s is not a valid buffer", s->s_name);
		x->l_buf = 0;
	}
}

void ipoke_int(t_ipoke *x, long n)
{
	if (x->l_obj.z_in == 2)
	{
		if (n)
			x->l_chan = (short)(CLIP(n,1,4) - 1);
		else
			x->l_chan = 0;
		x->l_index_precedent = -1;
	}
	else
		object_error((t_object *)x, "buffer~ channel assignation by the rightmost inlet");
}

void ipoke_interp(t_ipoke *x, long n)
{
	switch (n)
	{
		case 0:
			x->l_interp = 0;
			break;
		case 1:
			x->l_interp = 1;
			break;
		default:
			object_error((t_object *)x, "wrong interpolation type");
			break;
	}
}

void ipoke_overdub(t_ipoke *x, double n)
{
	x->l_overdub = n;
//	post("overdub level is %f", x->l_overdub = n);
}

void ipoke_dblclick(t_ipoke *x)
{
	t_buffer *b;
	
	b = (t_buffer *)(x->l_sym->s_thing);
	
	if ((b) && (ob_sym(b) == ps_buffer))
		mess0((t_object *)b,gensym("dblclick"));
}

void ipoke_assist(t_ipoke *x, void *b, long m, long a, char *s)
{
	switch (a)
	{	
		case 0:
			sprintf(s,"(signal) Value In");
			break;
		case 1:
			sprintf(s,"(signal) Sample Index");
			break;
		case 2:
			sprintf(s,"(int) Audio Channel In buffer~");
			break;
	}
}

inline long wrap_index(size_t index, size_t arrayLength)
{
	while(index >= arrayLength)
        index -= arrayLength;
    return index;
}